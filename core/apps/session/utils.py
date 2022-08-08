import calendar
import datetime
import json
import logging
import operator
import uuid
from copy import copy

from django.db import transaction
from django.db.models import Q

from core.apps.common.common_functions import CommonClass, get_actual_day_yesterday
from core.apps.common.const import (
    LOAD_CHANGE_LIMIT,
    MAX_REPEATED_INTENSITY,
    SQS_CHANGE_LIMIT,
)
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.messages import (
    CONSECUTIVE_HIGH_INTENSITY_SESSIONS_MESSAGE,
    HIGH_RECENT_TRAINING_LOAD_MESSAGE,
    HIGH_SINGLE_RIDE_LOAD_MESSAGE,
)
from core.apps.common.utils import (
    initialize_dict,
    read_s3_xlsx_file,
    update_is_active_value,
)
from core.apps.ctp.calculations import set_as_rest_day as set_rest_day
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.daily.serializers import (
    DayActualSessionSerializer,
    DayPlannedSessionSerializer,
)
from core.apps.evaluation.block_evaluation.dictionary import make_block_session_dict
from core.apps.evaluation.session_evaluation.dictionary import (
    get_evaluation_scores_dict,
)
from core.apps.evaluation.session_evaluation.models import (
    SessionScoreCategoriesTruthTable,
)
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.models import Notification
from core.apps.notification.services import update_move_session_notification
from core.apps.plan.enums.session_status_enum import (
    SessionLabelEnum,
    SessionLabelTypeEnum,
    SessionStatusEnum,
    SessionTypeEnum,
)
from core.apps.plan.models import UserPlan
from core.apps.week.models import UserWeek

from ..achievements.models import PersonalRecord
from ..activities.utils import dakghor_get_athlete_activity
from ..challenges.models import UserChallenge
from ..common.services import RoundServices
from ..common.tp_common_utils import (
    read_s3_pillar_cadence_data,
    read_s3_pillar_heart_rate_data,
    read_s3_pillar_power_data,
)
from .api.base.serializers import GetSessionIntervalsSerializer
from .enums.session_warning_type_enum import SessionWarningTypeEnum
from .models import ActualSession, PlannedSession, SessionScore

logger = logging.getLogger(__name__)
calendar.setfirstweekday(calendar.MONDAY)


def populate_planned_time_in_hr_zone(session):
    try:
        session_intervals = session.user_session_intervals.all()
    except Exception as e:
        logger.info("No interval found" + str(e))
        return

    planned_time_in_hr_zones = initialize_dict(0, 7)

    for session_interval in session_intervals:
        logger.info(
            f"Retrieving time in second from session interval: {session_interval.id}"
        )
        if session_interval.fthr_percentage_upper == 999:
            mid_fthr = session_interval.fthr_percentage_lower
        else:
            mid_fthr = (
                session_interval.fthr_percentage_lower
                + session_interval.fthr_percentage_upper
            ) / 2

        zone_focus = CommonClass.get_zone_focus_from_fthr(mid_fthr)
        planned_time_in_hr_zones[zone_focus]["value"] += int(
            session_interval.time_in_seconds
        )

    logger.info("Saving data in session")
    session.planned_time_in_hr_zone = json.dumps(planned_time_in_hr_zones)
    session.save()


def clear_current_weeks_sessions(user):
    from core.apps.daily.models import PlannedDay

    today = datetime.date.today()
    user_week = UserWeek.objects.filter(
        user_block__user_auth=user, start_date__lte=today, end_date__gte=today
    ).first()
    all_days = PlannedDay.objects.filter(week_code=user_week.week_code)
    active_days = PlannedDay.objects.filter(
        week_code=user_week.week_code, is_active=True
    )
    for day in active_days:
        first_day = all_days.filter(date=day.activity_date).first()
        planned_days = PlannedDay.objects.filter(user_auth=user, date=day.activity_date)
        update_is_active_value(planned_days, False)

        first_day.is_active = True
        first_day.save()
        first_session = PlannedSession.objects.filter(
            day_code=first_day.day_code
        ).first()
        if first_session:
            planned_sessions = PlannedSession.objects.filter(
                user_auth=user, session_date_time=day.activity_date
            )
            update_is_active_value(planned_sessions, False)
            first_session.is_active = True
            first_session.save()


def set_planned_session(user_session, day_code):
    planned_session = PlannedSession()
    session_code = uuid.uuid4()

    planned_session.name = user_session.name
    planned_session.user_auth = user_session.user_auth
    planned_session.user_id = user_session.user_auth.code
    planned_session.session_type = user_session.session_type
    planned_session.session = user_session.session
    planned_session.pad_time_in_seconds = user_session.pad_time_in_seconds
    planned_session.pad_pss = user_session.pad_pss
    planned_session.is_pad_applicable = user_session.is_pad_applicable
    planned_session.zone_focus = user_session.zone_focus
    planned_session.session_date_time = user_session.session_date_time
    planned_session.day_code = day_code
    planned_session.session_code = session_code
    planned_session.planned_duration = user_session.planned_duration
    planned_session.planned_pss = user_session.planned_pss
    planned_session.planned_load = user_session.planned_load
    planned_session.planned_acute_load = user_session.planned_acute_load
    planned_session.planned_intensity = user_session.planned_intensity
    planned_session.description = user_session.description
    planned_session.planned_time_in_power_zone = user_session.planned_time_in_power_zone
    planned_session.planned_time_in_hr_zone = user_session.planned_time_in_hr_zone
    planned_session.is_active = user_session.is_active
    planned_session.created_at = user_session.created_at
    planned_session.updated_at = user_session.updated_at

    planned_session.save()
    return session_code


def set_garmin_data(user_session):
    garmin_data = user_session.garmin_data
    garmin_data.ride_summary = user_session.ride_summary
    garmin_data.weighted_power = user_session.weighted_power
    garmin_data.save()

    return garmin_data


def set_session_score(user_session):
    session_score = SessionScore()
    session_score.sqs_today_score = user_session.sqs_today_score
    session_score.prs_score = user_session.prs_score
    session_score.overall_score = user_session.overall_score
    session_score.duration_score = user_session.duration_score
    session_score.sqs_session_score = user_session.sqs_session_score
    session_score.pss_score = user_session.pss_score
    session_score.save()

    return session_score


def set_actual_session(user_session, day_code, session_code):
    session_score = set_session_score(user_session=user_session)
    actual_session = ActualSession()
    actual_session.garmin_data = user_session.garmin_data
    actual_session.session_date_time = user_session.session_date_time
    actual_session.day_code = day_code
    actual_session.actual_duration = user_session.actual_duration
    actual_session.actual_pss = user_session.actual_pss
    actual_session.actual_load = user_session.actual_load
    actual_session.actual_acute_load = user_session.actual_acute_load
    actual_session.actual_intensity = user_session.actual_intensity
    actual_session.actual_distance_in_meters = user_session.actual_distance_in_meters
    actual_session.session_score = session_score
    actual_session.session_code = session_code
    actual_session.is_active = user_session.is_active
    actual_session.user_auth = user_session.user_auth
    actual_session.user_id = user_session.user_auth.code
    actual_session.save()

    return actual_session


def flag_unusual_load_sqs_drop(user, user_local_date):
    """Checks if the user's actual load or SQS has changed more than change_limit and flags it if it does"""
    try:
        actual_day = user.actual_days.get(activity_date=user_local_date, is_active=True)
    except ActualDay.DoesNotExist:
        return False
    except Exception as ex:
        logger.error(
            f"User: {user.id}, activity date: {user_local_date}, Exception: {str(ex)}"
        )
        return True

    previous_day, _ = get_actual_day_yesterday(user, user_local_date)
    if (
        previous_day.actual_load - actual_day.actual_load > LOAD_CHANGE_LIMIT
        or previous_day.sqs_today - actual_day.sqs_today > SQS_CHANGE_LIMIT
    ):
        return True

    return False


def is_session_completed(session):
    return ActualSession.objects.filter(session_code=session.session_code).exists()


def move_planned_session(request, user):
    not_permitted_msg = "Not permitted, trying to move session of other user or day"
    day_not_found_msg = "No user day found with the id"
    session_not_found_msg = "No user session found with the id"
    err_msg = "Session could not move"
    recovery_session_msg = "Recovery session is not movable"
    out_of_week_msg = "Can't move session out of current week"
    completed_session_msg = "Completed session can't me moved"

    session_pk = request.data["session_id"]
    target_day_pk = request.data["day_id"]
    try:
        session = PlannedSession.objects.get(pk=session_pk)
    except Exception as e:
        logger.exception(str(e))
        return True, err_msg, session_not_found_msg
    else:
        user_local_date = user.user_local_date
        today_day = PlannedDay.objects.get(
            user_auth=user, activity_date=user_local_date, is_active=True
        )
        current_week = UserWeek.objects.get(
            week_code=today_day.week_code, is_active=True
        )
        if (
            session.session_date_time.date() < current_week.start_date
            or session.session_date_time.date() > current_week.end_date
        ):
            return True, err_msg, out_of_week_msg
        if session.user_auth != user:
            return True, err_msg, not_permitted_msg
        if session.session_type.code == "REST":
            return True, err_msg, recovery_session_msg
        if is_session_completed(session):
            return True, err_msg, completed_session_msg
    try:
        target_day = PlannedDay.objects.get(pk=target_day_pk, is_active=True)
    except Exception as e:
        logger.exception(str(e))
        return True, err_msg, day_not_found_msg
    else:
        if target_day.user_auth != user:
            return True, err_msg, not_permitted_msg

    if session and target_day:
        # make the source day session inactive
        session.is_active = False
        session.save()

        # make the source day sessions inactive and create a recovery day
        source_day = PlannedDay.objects.get(day_code=session.day_code, is_active=True)
        yesterday = source_day.previous_day
        source_day.yesterday = yesterday
        actual_yesterday = None
        if yesterday:
            actual_yesterday = ActualDay.objects.filter(
                activity_date=yesterday.activity_date, is_active=True, user_auth=user
            ).last()
        user_plan = user.user_plans.filter(is_active=True).last()
        user_personalise_data = user.personalise_data.filter(is_active=True).last()
        source_day, rest_session = set_rest_day(
            user_plan,
            source_day,
            user_personalise_data,
            utp=False,
            actual_yesterday=actual_yesterday,
        )
        source_day.zone_focus = rest_session.session_type.target_zone
        source_day.save()
        rest_session.day_code = source_day.day_code
        rest_session.save()

        # make the destination day sessions inactive and assign source session to this day
        planned_sessions = PlannedSession.objects.filter(day_code=target_day.day_code)
        update_is_active_value(planned_sessions, False)

        target_day.zone_focus = session.session_type.target_zone
        target_day.save()

        # make a new session with exactly the values of the session to be moved
        # assign it to the newly created target day
        moved_session_dict = session.__dict__
        del moved_session_dict["_state"]
        del moved_session_dict["id"]
        moved_session = PlannedSession.objects.create(**moved_session_dict)
        moved_session.is_active = True
        moved_session.day_code = target_day.day_code
        moved_session.session_date_time = target_day.activity_date
        moved_session.save()
        if user_local_date in [source_day.activity_date, target_day.activity_date]:
            update_move_session_notification(user, source_day, moved_session)

    return False, "Session moved successfully", None


def delete_planned_session(request, user):
    not_permitted_msg = "Not permitted, trying to delete others session"
    recovery_day_msg = "You are trying to cancel a rest day"
    not_cancelled_msg = "Couldn't cancel the session"
    successful_cancel_msg = "Session cancelled successfully"

    session_id = request.data["session_id"]
    session = PlannedSession.objects.get(id=session_id)

    if session.user_auth != user:
        return True, not_permitted_msg, None
    if session.session_type.code == "REST":
        return True, recovery_day_msg, None

    session.is_active = False
    session.save()
    day = PlannedDay.objects.get(day_code=session.day_code, is_active=True)

    try:
        yesterday = day.previous_day
        day.yesterday = yesterday
        actual_yesterday = None
        if yesterday:
            actual_yesterday = ActualDay.objects.filter(
                activity_date=yesterday.activity_date, is_active=True, user_auth=user
            ).last()
        user_plan = user.user_plans.filter(is_active=True).last()
        user_personalise_data = user.personalise_data.filter(is_active=True).last()
        day, session = set_rest_day(
            user_plan,
            day,
            user_personalise_data,
            utp=False,
            actual_yesterday=actual_yesterday,
        )
        day.zone_focus = session.session_type.target_zone
        day.save()
        session.day_code = day.day_code
        session.save()
    except Exception as e:
        logger.error(f"{not_cancelled_msg}. Exception: {str(e)}")
        return True, not_cancelled_msg, None

    return False, successful_cancel_msg, None


# def binary_search(a, x, lo=0, hi=None):
#     if hi is None:
#         hi = len(a)
#     while lo < hi:
#         mid = (lo+hi)//2
#         if a[mid].session_date_time.date() < x:
#             lo = mid+1
#         else:
#             hi = mid
#     if lo != len(a) and a[lo].session_date_time.date() == x:
#         return a[lo]
#     return None


def get_actual_session_for_recovery_session(
    planned_session, actual_sessions, actual_session_index, actual_sessions_len
):
    j = actual_session_index
    actual_session = None
    if (
        j < actual_sessions_len
        and planned_session.session_code == actual_sessions[j].session_code
    ):
        actual_session = actual_sessions[j]
        j += 1
    # Check if there are any unplanned session on that day
    if (
        j < actual_sessions_len
        and actual_sessions[j].is_unplanned_session()
        and actual_sessions[j].session_date_time.date()
        == planned_session.session_date_time.date()
    ):
        actual_session = actual_sessions[j]
        j += 1

    return actual_session, j


def get_actual_session_for_non_recovery_session(
    planned_session, actual_sessions, actual_session_index, actual_sessions_len
):
    j = actual_session_index
    actual_session = None
    if (
        j < actual_sessions_len
        and planned_session.session_code == actual_sessions[j].session_code
    ):
        actual_session = actual_sessions[j]
        j += 1

    return actual_session, j


# Deprecated from R7
def map_actual_session_into_planned_session(
    planned_sessions, actual_sessions, timezone_offset
):
    """This function is coded in this way to improve performance of the api.
    TODO: If better approach found with same/better performance need to refactor it
    """
    block_session_dict_arr = []
    # block_start = time.perf_counter()
    actual_sessions_len = len(actual_sessions)

    if not actual_sessions_len:
        block_session_dict_arr = [
            make_block_session_dict(planned_session, None, timezone_offset)
            for planned_session in planned_sessions
        ]
    else:
        j = 0  # actual_sessions_index
        planned_sessions_len = len(planned_sessions)
        for i in range(planned_sessions_len):
            # Skip unnecessary actual sessions
            planned_date_time = planned_sessions[i].session_date_time.date()
            while (
                j < actual_sessions_len
                and actual_sessions[j].session_date_time.date() < planned_date_time
            ):
                j += 1

            if planned_sessions[i].is_recovery_session():
                actual_session, j = get_actual_session_for_recovery_session(
                    planned_sessions[i], actual_sessions, j, actual_sessions_len
                )
            else:
                actual_session, j = get_actual_session_for_non_recovery_session(
                    planned_sessions[i], actual_sessions, j, actual_sessions_len
                )

            block_session_dict = make_block_session_dict(
                planned_sessions[i], actual_session, timezone_offset
            )
            block_session_dict_arr.append(block_session_dict)

    return block_session_dict_arr


def get_block_session_dict(planned_sessions, user):
    """Returns session dicts of training blocks"""
    block_session_dict_arr = []
    for planned_session in planned_sessions:
        actual_session = planned_session.actual_session
        if actual_session and actual_session.third_party:
            block_session_dict_arr.append(
                DayActualSessionSerializer(
                    actual_session,
                    context={
                        "user": user,
                        # 'event_dates': event_dates
                    },
                ).data
            )
        else:
            block_session_dict_arr.append(
                DayPlannedSessionSerializer(
                    planned_session,
                    context={
                        "user": user,
                        # 'event_dates': event_dates
                    },
                ).data
            )

    return block_session_dict_arr


def ftp_fthr_details(user_personalise_data, cur_ftp, cur_fthr):
    is_power_meter_available = (
        user_personalise_data.is_power_meter_available
    )  # Deprecated from R7

    is_ftp_available = True if cur_ftp else False
    is_fthr_available = True

    return is_power_meter_available, is_ftp_available, is_fthr_available


def get_evaluation_scores(planned_session, actual_session):
    from core.apps.evaluation.session_evaluation.utils import (
        get_evaluation_scores_comment,
    )

    if planned_session:
        session_scores_tt = SessionScoreCategoriesTruthTable.objects.all().order_by(
            "id"
        )
        evaluation_scores_comment = get_evaluation_scores_comment(
            actual_session, session_scores_tt
        )
        evaluation_scores_dict = get_evaluation_scores_dict(
            actual_session, planned_session, evaluation_scores_comment
        )

        return evaluation_scores_dict
    else:
        return []


def get_planned_power_and_hr_zone_data(planned_session):
    planned_time_in_power_zones_dict = (
        json.loads(planned_session.planned_time_in_power_zone)
        if planned_session.planned_time_in_power_zone
        else initialize_dict(0, 8)
    )
    for zone in planned_time_in_power_zones_dict:
        zone["value"] = int(zone["value"])

    planned_time_in_hr_zones_dict = (
        json.loads(planned_session.planned_time_in_hr_zone)
        if planned_session.planned_time_in_hr_zone
        else initialize_dict(0, 7)
    )
    for zone in planned_time_in_hr_zones_dict:
        zone["value"] = int(zone["value"])

    return planned_time_in_power_zones_dict, planned_time_in_hr_zones_dict


def get_actual_power_and_hr_zone_data(
    actual_session, actual_time_in_power_zones_dict, actual_time_in_hr_zones_dict
):
    if actual_session.athlete_activity_code is None:
        return actual_time_in_power_zones_dict, actual_time_in_hr_zones_dict

    athlete_activity = dakghor_get_athlete_activity(
        actual_session.athlete_activity_code
    ).json()["data"]["athlete_activity"]
    actual_time_in_power_zones_dict = json.loads(athlete_activity["time_in_power_zone"])
    actual_time_in_hr_zones_dict = json.loads(
        athlete_activity["time_in_heart_rate_zone"]
    )
    return actual_time_in_power_zones_dict, actual_time_in_hr_zones_dict


def get_planned_session_interval_data(planned_session, cur_ftp, cur_fthr, max_hr):
    try:
        if planned_session.is_pad_applicable:
            session_intervals = planned_session.session.session_intervals.filter(
                Q(time_in_seconds__gt=0) | Q(is_padding_interval=True)
            ).order_by("id")
        else:
            session_intervals = planned_session.session.session_intervals.filter(
                Q(time_in_seconds__gt=0)
            ).order_by("id")

        serialized_session_intervals = GetSessionIntervalsSerializer(
            session_intervals,
            many=True,
            context={
                "user_ftp": cur_ftp,
                "user_fthr": cur_fthr,
                "max_hr": max_hr,
                "is_pad_applicable": planned_session.is_pad_applicable,
                "pad_time_in_seconds": planned_session.pad_time_in_seconds,
            },
        )
        return serialized_session_intervals.data
    except Exception as e:
        logger.exception(f"{str(e)}. User ID: {str(planned_session.user_auth.id)}")
        return []


def get_average(actual_data_by_second):
    actual_data_len = len(actual_data_by_second)
    if actual_data_len <= 0:
        return 0
    average_value = (
        sum(map(operator.itemgetter("value"), actual_data_by_second)) / actual_data_len
    )
    return average_value


def get_actual_session_interval_data(planned_intervals, athlete_activity):
    if athlete_activity is None or not planned_intervals:
        return []

    s3_pillar_file_path = athlete_activity["pillar_file"]
    worksheet = read_s3_xlsx_file(s3_pillar_file_path)

    actual_power_by_second = read_s3_pillar_power_data(worksheet)
    actual_hr_by_second = read_s3_pillar_heart_rate_data(worksheet)
    actual_cadence_by_second = read_s3_pillar_cadence_data(worksheet)

    actual_intervals = []
    last_index = -1
    for planned_interval in planned_intervals:
        planned_duration_in_seconds = planned_interval["duration"]
        if planned_duration_in_seconds <= 0:
            continue
        first_index = last_index + 1
        last_index = first_index + planned_duration_in_seconds - 1
        average_power = get_average(actual_power_by_second[first_index:last_index])
        average_hr = get_average(actual_hr_by_second[first_index:last_index])
        average_cadence = get_average(actual_cadence_by_second[first_index:last_index])
        actual_interval = {
            "description": planned_interval["description"],
            "duration": round(planned_interval["duration"]),
            "power": round(average_power),
            "heart_rate": round(average_hr),
            "cadence": round(average_cadence),
        }
        actual_intervals.append(actual_interval)
    return actual_intervals


def get_session_metadata(actual_session, planned_session=None, planned_id=None):
    # TODO: Try to make a single function for retrieving session metadata everywhere
    actual_id = actual_session.id if actual_session else None
    if not planned_id:
        planned_id = planned_session.id if planned_session else None
    is_manual_activity = (
        True
        if actual_session
        and actual_session.third_party.code == ThirdPartySources.MANUAL.value[0]
        else False
    )
    session_label = get_session_label(actual_session, planned_id)

    if planned_id and actual_id:
        session_type = SessionTypeEnum.CYCLING.value
        session_status = SessionStatusEnum.PAIRED.value
    elif planned_id:
        session_type = SessionTypeEnum.CYCLING.value
        session_status = SessionStatusEnum.PLANNED.value
    else:
        session_type = (
            actual_session and actual_session.activity_type
        ) or SessionTypeEnum.CYCLING.value
        session_status = SessionStatusEnum.UNPAIRED.value

    return {
        "planned_id": planned_id,
        "actual_id": actual_id,
        "session_type": session_type.upper(),
        "session_status": session_status,
        "session_label": session_label,
        "is_manual_activity": is_manual_activity,
        "session_label_type": actual_session.session_label if actual_session else None,
    }


def get_session_local_time(actual_session, planned_session, user):
    if actual_session:
        return actual_session.session_date_time

    return DateTimeUtils.get_user_local_date_time_from_utc(
        user.timezone_offset, planned_session.session_date_time
    )


def get_session_name(
    actual_session,
    planned_session,
    session_date_time,
    event_date=False,
    activity_type=None,
):
    if actual_session and planned_session and event_date:
        return actual_session.user_plan.user_event.name
    elif actual_session and actual_session.activity_name:
        return actual_session.activity_name
    elif planned_session:
        return planned_session.name
    elif datetime.time(hour=0) <= session_date_time.time() < datetime.time(hour=12):
        time_of_day = "Morning"
    elif session_date_time.time() < datetime.time(hour=17):
        time_of_day = "Afternoon"
    else:
        time_of_day = "Evening"

    return f"My {time_of_day} {ActivityTypeEnum.get_pillar_defined_message_text(activity_type=activity_type)}"


def get_session_label(actual_session, planned_id=None):
    if actual_session:
        if actual_session.session_label == SessionLabelTypeEnum.TRAINING_SESSION:
            return (
                SessionLabelEnum.EVALUATED_SESSION
                if (actual_session and planned_id)
                else SessionLabelEnum.COMPLETED_SESSION
            )
        elif actual_session.session_label == SessionLabelTypeEnum.COMMUTE:
            return (
                SessionLabelEnum.EVALUATED_COMMUTE
                if (actual_session and planned_id)
                else SessionLabelEnum.COMPLETED_COMMUTE
            )
        else:
            return (
                SessionLabelEnum.EVALUATED_EVENT
                if (actual_session and planned_id)
                else SessionLabelEnum.COMPLETED_EVENT
            )
    else:
        return SessionLabelEnum.PLANNED_SESSION


def get_manual_activity_ride_summary(pillar_data):
    manual_ride_summary = []
    if pillar_data.average_heart_rate:
        manual_ride_summary.append(
            {
                "type": "Heart Rate",
                "unit": "bpm",
                "average": str(pillar_data.average_heart_rate),
            }
        )
    if pillar_data.average_speed:
        manual_ride_summary.append(
            {
                "type": "Speed",
                "unit": "km/h",
                "average": str(round(pillar_data.average_speed, 1)),
            }
        )
    if pillar_data.average_power:
        manual_ride_summary.append(
            {"type": "Power", "unit": "W", "average": str(pillar_data.average_power)}
        )
    return manual_ride_summary


def get_edit_manual_activity_data(actual_session):
    pillar_data = actual_session.pillar_data
    return {
        "duration": round(actual_session.actual_duration * 60),
        "distance": round(actual_session.actual_distance_in_meters / 1000, 1),
        "average_speed": round(pillar_data.average_speed, 1) if pillar_data else None,
        "average_heart_rate": pillar_data.average_heart_rate if pillar_data else None,
        "average_power": pillar_data.average_power if pillar_data else None,
    }


def get_session_warnings(actual_session):
    """Returns the active warnings related to the actual session"""
    round_load = RoundServices.round_load
    round_pss = RoundServices.round_pss
    round_intensity = RoundServices.round_intensity

    notifications = Notification.objects.filter(
        data=actual_session.code, is_active=True
    )
    session_date = actual_session.session_date_time.date()
    yesterday_date = session_date - datetime.timedelta(days=1)
    actual_session_day = ActualDay.objects.filter(
        user_auth=actual_session.user_auth, is_active=True, activity_date=session_date
    ).last()
    actual_yesterday, _ = get_actual_day_yesterday(
        actual_session.user_auth, yesterday_date
    )
    yesterday_high_intensity_session = ActualSession.objects.filter(
        user_auth=actual_session.user_auth,
        session_date_time__date=yesterday_date,
        is_active=True,
        actual_intensity__gt=MAX_REPEATED_INTENSITY,
    ).last()
    warnings = []

    for notification in notifications:
        if (
            notification.notification_type_id
            == NotificationTypeEnum.HIGH_SINGLE_RIDE_LOAD.value[0]
        ):
            warning = {
                "type": SessionWarningTypeEnum.PSS,
                "title": NotificationTypeEnum.HIGH_SINGLE_RIDE_LOAD.value[1],
                "message": HIGH_SINGLE_RIDE_LOAD_MESSAGE.format(
                    round_load(actual_yesterday.actual_load),
                    round_pss(actual_session.actual_pss),
                ),
            }
            warnings.append(warning)
        elif (
            notification.notification_type_id
            == NotificationTypeEnum.HIGH_RECENT_TRAINING_LOAD.value[0]
        ):
            warning = {
                "type": SessionWarningTypeEnum.FRESHNESS,
                "title": NotificationTypeEnum.HIGH_RECENT_TRAINING_LOAD.value[1],
                "message": HIGH_RECENT_TRAINING_LOAD_MESSAGE.format(
                    round_load(actual_session_day.actual_load),
                    round_load(actual_session_day.actual_acute_load),
                ),
            }
            warnings.append(warning)
        elif (
            notification.notification_type_id
            == NotificationTypeEnum.CONSECUTIVE_HIGH_INTENSITY_SESSIONS.value[0]
        ):
            warning = {
                "type": SessionWarningTypeEnum.INTENSITY,
                "title": NotificationTypeEnum.CONSECUTIVE_HIGH_INTENSITY_SESSIONS.value[
                    1
                ],
                "message": CONSECUTIVE_HIGH_INTENSITY_SESSIONS_MESSAGE.format(
                    round_intensity(
                        yesterday_high_intensity_session.actual_intensity * 100
                    ),
                    round_intensity(actual_session.actual_intensity * 100),
                ),
            }
            warnings.append(warning)

    return warnings


def get_event_day_planned_sessions(user):
    event_dates = list(
        UserPlan.objects.filter(user_auth=user, is_active=True).values_list(
            "end_date", flat=True
        )
    )
    return PlannedSession.objects.filter(
        user_auth=user, is_active=True, session_date_time__date__in=event_dates
    )


def update_achievement_data(user, actual_session):
    """Updates achievements (Personal record, challenge/trophy) for edit/delete session"""
    personal_records = PersonalRecord.objects.filter(
        actual_session_code=actual_session.code, is_active=True
    )
    update_is_active_value(personal_records, False)

    user_challenge = UserChallenge.objects.filter(
        user_auth=user,
        is_active=True,
        challenge__start_date__lte=actual_session.session_date_time,
        challenge__end_date__gte=actual_session.session_date_time.date(),
    ).last()
    if user_challenge:
        user_challenge.achieved_value -= actual_session.actual_distance_in_meters
        user_challenge.save()


def check_if_intervals_repeat(intervals):
    """Checks if there is any repetition of session intervals from start_position"""
    intervals_length = len(intervals)

    # Check if there is a repeating sequence here. Check every sequence length which is lower or equal to half the
    # remaining list length (Otherwise it'll get out of bounds)
    start_position = 0
    sequence_length = 1
    while sequence_length <= (intervals_length - start_position) / 2:
        # Check if the sequences of length sequence_length which start at start_position
        # and (start_position + sequence_length (the one immediately following it)) are equal
        sequences_are_equal = True
        for i in range(sequence_length):
            if not same_session_interval(
                intervals[start_position + i],
                intervals[start_position + sequence_length + i],
            ):
                sequences_are_equal = False
                break

        if sequences_are_equal:
            logger.info(
                f"Repeat steps are detected of sequence length {sequence_length}"
            )
            return True, sequence_length
        sequence_length += 1

    return False, None


def same_session_interval(first_interval, second_interval):
    return (
        first_interval.name == second_interval.name
        and first_interval.time_in_seconds == second_interval.time_in_seconds
        and first_interval.ftp_percentage_lower == second_interval.ftp_percentage_lower
        and first_interval.ftp_percentage_upper == second_interval.ftp_percentage_upper
    )


@transaction.atomic
def update_user_actual_session_date_time_fields(user):
    actual_sessions = user.actual_sessions.filter()
    for actual_session in actual_sessions:
        current_session_date_time = copy(actual_session.session_date_time)
        if actual_session.utc_session_date_time:
            actual_session.session_date_time = actual_session.utc_session_date_time
        else:
            actual_session.session_date_time = (
                DateTimeUtils.get_user_local_date_time_from_utc(
                    user.timezone_offset, current_session_date_time
                )
            )
        actual_session.utc_session_date_time = current_session_date_time
        actual_session.save()
