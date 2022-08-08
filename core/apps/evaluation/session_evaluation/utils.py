import json
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q

from core.apps.activities.utils import dakghor_get_athlete_activity
from core.apps.calculations.evaluation.absolute_difference_duration_services import (
    AbsoluteDifferenceDurationService,
)
from core.apps.calculations.evaluation.absolute_difference_intensity_services import (
    AbsoluteDifferenceIntensityService,
)
from core.apps.calculations.evaluation.absolute_difference_pss_services import (
    AbsoluteDifferencePssService,
)
from core.apps.calculations.evaluation.acute_load_services import AcuteLoadService
from core.apps.calculations.evaluation.duration_score_services import (
    DurationScoreService,
)
from core.apps.calculations.evaluation.intensity_services import IntensityService
from core.apps.calculations.evaluation.load_services import LoadService
from core.apps.calculations.evaluation.prs_services import PrsService
from core.apps.calculations.evaluation.pss_score_services import PssScoreService
from core.apps.calculations.evaluation.pss_services import PssService
from core.apps.calculations.evaluation.session_accuracy_score_services import (
    SessionAccuracyScoreService as SASService,
)
from core.apps.calculations.evaluation.session_overall_score_services import (
    SessionOverallScoreService,
)
from core.apps.calculations.evaluation.sqs_services import (
    SQSSessionService,
    SqsTodayService,
    WeightingSqsService,
)
from core.apps.common.common_functions import CommonClass, get_actual_day_yesterday
from core.apps.common.const import (
    MAX_REPEATED_INTENSITY,
    MAX_SINGLE_RIDE_MULTIPLIER,
    MINIMUM_FRESHNESS,
)
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.messages import (
    OVERTRAINING_NOTIFICATION_BODY,
    OVERTRAINING_NOTIFICATION_TITLE,
)
from core.apps.common.tp_common_utils import (
    read_s3_pillar_compressed_hr_data,
    read_s3_pillar_compressed_power_data,
)
from core.apps.common.utils import (
    create_new_model_instance,
    get_fthr_from_max_heart_rate,
    get_obj_recovery_index,
    get_ride_summary,
    initialize_dict,
    read_s3_xlsx_file,
)
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.daily.utils import get_acute_load_constant, get_load_constant
from core.apps.evaluation.daily_evaluation.utils import set_actual_day_data
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.services import create_notification
from core.apps.session.models import (
    ActualSession,
    PlannedSession,
    SessionScore,
    create_actual_session,
)
from core.apps.user_profile.utils import (
    get_user_fthr,
    get_user_ftp,
    get_user_max_heart_rate,
)

from ...common.enums.activity_type import ActivityTypeEnum
from .dictionary import (
    get_evaluation_scores_dict,
    get_hr_data_dict_with_threshold,
    get_power_data_dict_with_threshold,
    get_session_details_dict_other_data,
    get_session_graph_data_dict,
    get_session_info_dict,
)
from .models import SessionScoreCategoriesTruthTable

logger = logging.getLogger(__name__)


def get_planned_session_for_graph(user, planned_id):
    if not planned_id:
        return None

    planned_session = PlannedSession.objects.filter(pk=planned_id).last()
    if not planned_session.is_active:
        planned_session = user.planned_sessions.filter(
            session_code=planned_session.session_code, is_active=True
        ).last()
    return planned_session


def get_actual_session(user, actual_id):
    if not actual_id:
        return None

    actual_session = ActualSession.objects.filter(pk=actual_id).last()
    actual_session = ActualSession.objects.filter_actual_sessions_with_time_range(
        user_auth=user, session_date_time=actual_session.session_date_time
    )
    return actual_session


def get_manual_activity(user, actual_id):
    if not actual_id:
        return None

    actual_session = user.actual_sessions.filter(pk=actual_id).last()
    if not actual_session.is_active:
        actual_session = user.actual_sessions.filter(
            code=actual_session.code, is_active=True
        ).last()
    return actual_session


def get_session_details_graph_data_with_threshold(
    user, planned_id, total_point, actual_id=None
):
    planned_session = get_planned_session_for_graph(user, planned_id)

    if not actual_id:
        logger.info(f"Actual session id not provided. Planned session id: {planned_id}")

        if planned_session.zone_focus:
            actual_session = planned_session.actual_session
        else:
            unplanned_session = (
                ActualSession.objects.filter(
                    user_auth=user,
                    is_active=True,
                    session_code=None,
                    session_date_time__date=planned_session.session_date_time.date(),
                )
                .order_by("session_date_time")
                .first()
            )
            actual_session = unplanned_session if unplanned_session else None
    else:
        actual_session = get_actual_session(user, actual_id)

    session_date_time = (
        actual_session.session_date_time
        if actual_session
        else planned_session.session_date_time
    )

    cur_ftp = get_user_ftp(user, session_date_time)
    cur_fthr = get_user_fthr(user, session_date_time)
    max_heart_rate = get_user_max_heart_rate(user, session_date_time)

    actual_power_data_dict = []
    actual_hr_data_dict = []
    if actual_session and actual_session.athlete_activity_code:
        s3_pillar_file_path = dakghor_get_athlete_activity(
            actual_session.athlete_activity_code
        ).json()["data"]["athlete_activity"]["pillar_file"]
        worksheet = read_s3_xlsx_file(s3_pillar_file_path)

        if cur_ftp:
            actual_power_data_dict = read_s3_pillar_compressed_power_data(worksheet)
        actual_hr_data_dict = read_s3_pillar_compressed_hr_data(worksheet)

    planned_power_data_dict = []
    planned_hr_data_dict = []
    if planned_session:
        if planned_session.is_pad_applicable:
            session_intervals = planned_session.session.session_intervals.filter(
                Q(time_in_seconds__gt=0) | Q(is_padding_interval=True)
            ).order_by("id")
        else:
            session_intervals = planned_session.session.session_intervals.filter(
                Q(time_in_seconds__gt=0)
            ).order_by("id")

        if session_intervals:
            planned_power_data = get_session_intervals_power_data(
                cur_ftp,
                session_intervals,
                planned_session.is_pad_applicable,
                planned_session.pad_time_in_seconds,
            )
            planned_power_data_dict = get_power_data_dict_with_threshold(
                planned_power_data, cur_ftp, total_point
            )

            planned_hr_data = get_session_intervals_hr_data(
                cur_fthr,
                max_heart_rate,
                session_intervals,
                planned_session.is_pad_applicable,
                planned_session.pad_time_in_seconds,
            )
            planned_hr_data_dict = get_hr_data_dict_with_threshold(
                planned_hr_data, cur_fthr, max_heart_rate, total_point
            )

    # Deprecated from R7
    user_personalise_data = user.personalise_data.filter(is_active=True).first()
    is_power_meter_available = user_personalise_data.is_power_meter_available

    is_ftp_available = bool(cur_ftp)
    is_fthr_available = True

    session_details_dict = get_session_graph_data_dict(
        actual_power_data_dict,
        planned_power_data_dict,
        actual_hr_data_dict,
        planned_hr_data_dict,
        is_ftp_available,
        is_fthr_available,
        is_power_meter_available,
    )
    return session_details_dict


# Deprecated from R8
def get_session_details_other_data(user, planned_session, actual_session=None):
    if not actual_session:
        if planned_session.is_recovery_session():
            unplanned_session = (
                ActualSession.objects.filter(
                    user_auth=user,
                    is_active=True,
                    session_code=None,
                    session_date_time__date=planned_session.session_date_time.date(),
                )
                .order_by("session_date_time")
                .first()
            )
            actual_session = (
                unplanned_session
                if unplanned_session
                else planned_session.actual_session
            )
        else:
            actual_session = planned_session.actual_session

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
    else:
        evaluation_scores_dict = []

    activity_time = actual_session.session_date_time.strftime("%Y-%m-%d %H:%M:%S")

    actual_time_in_power_zones_dict = initialize_dict(0, 8)
    actual_time_in_hr_zones_dict = initialize_dict(0, 7)
    ride_summary_dict = []

    if actual_session and actual_session.athlete_activity_code:
        athlete_activity = dakghor_get_athlete_activity(
            actual_session.athlete_activity_code
        ).json()["data"]["athlete_activity"]
    else:
        athlete_activity = None

    is_ftp_input_needed = False
    is_fthr_input_needed = False

    user_personalise_data = user.personalise_data.filter(is_active=True).first()
    cur_ftp = user_personalise_data.current_ftp
    cur_fthr = user_personalise_data.current_fthr

    if actual_session:
        activity_time = actual_session.session_date_time.strftime("%Y-%m-%d %H:%M:%S")
        if athlete_activity:
            if athlete_activity["time_in_power_zone"]:
                actual_time_in_power_zones_dict = json.loads(
                    athlete_activity["time_in_power_zone"]
                )
                if is_time_spent_in_zone(actual_time_in_power_zones_dict):
                    is_ftp_input_needed = not bool(
                        cur_ftp or user_personalise_data.ftp_input_denied
                    )

                for zone in actual_time_in_power_zones_dict:
                    zone["value"] = int(zone["value"])

            if athlete_activity["time_in_heart_rate_zone"]:
                actual_time_in_hr_zones_dict = json.loads(
                    athlete_activity["time_in_heart_rate_zone"]
                )
                if is_time_spent_in_zone(actual_time_in_hr_zones_dict):
                    is_fthr_input_needed = not bool(
                        cur_fthr or user_personalise_data.fthr_input_denied
                    )

                for zone in actual_time_in_hr_zones_dict:
                    zone["value"] = int(zone["value"])
            ride_summary_dict = get_ride_summary(athlete_activity["ride_summary"])
        elif actual_session.third_party.code == ThirdPartySources.MANUAL.value[0]:
            ride_summary_dict = get_manual_activity_ride_summary(
                actual_session.pillar_data
            )

    activity_info = get_activity_info(
        actual_session, athlete_activity, user_personalise_data
    )
    if planned_session:
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
    else:
        planned_time_in_power_zones_dict = []
        planned_time_in_hr_zones_dict = []

    # Deprecated from R7
    is_power_meter_available = user_personalise_data.is_power_meter_available

    is_ftp_available = True if cur_ftp else False
    is_fthr_available = True

    session_details_dict = get_session_details_dict_other_data(
        evaluation_scores_dict,
        actual_time_in_power_zones_dict,
        actual_time_in_hr_zones_dict,
        planned_time_in_power_zones_dict,
        planned_time_in_hr_zones_dict,
        ride_summary_dict,
        is_power_meter_available,
        is_ftp_available,
        is_fthr_available,
        activity_info,
        is_ftp_input_needed,
        is_fthr_input_needed,
        activity_time,
    )
    return session_details_dict


def get_session_intervals_power_data(
    cur_ftp, session_intervals, is_pad_applicable, time
):
    if cur_ftp is None:
        return []
    planned_power_data_list = []

    for interval in session_intervals:
        if interval.is_padding_interval is True:
            if is_pad_applicable is False:
                continue
            else:
                interval_duration = time
        else:
            interval_duration = interval.time_in_seconds
        power = (
            ((interval.ftp_percentage_lower + interval.ftp_percentage_upper) / 2) / 100
        ) * cur_ftp
        zone_focus = CommonClass.get_zone_focus_from_power(cur_ftp, power)

        for _ in range(int(interval_duration)):
            power_dict = {"value": power, "zone_focus": zone_focus}
            planned_power_data_list.append(power_dict)

    return planned_power_data_list


def get_session_intervals_hr_data(
    cur_fthr, max_heart_rate, session_intervals, is_pad_applicable, time
):
    planned_hr_data_list = []

    for interval in session_intervals:
        if interval.is_padding_interval is True:
            if is_pad_applicable is False:
                continue
            else:
                interval_duration = time
        else:
            interval_duration = interval.time_in_seconds

        if cur_fthr:
            hr = interval.get_hr_from_fthr(cur_fthr)
            zone_focus = CommonClass.get_zone_focus_from_hr(cur_fthr, hr)
        else:
            hr = interval.get_hr_from_max_heart_rate(max_heart_rate)
            zone_focus = CommonClass.get_zone_focus_from_hr_by_max_hr(
                max_heart_rate, hr
            )

        for _ in range(int(interval_duration)):
            power_dict = {"value": hr, "zone_focus": zone_focus}
            planned_hr_data_list.append(power_dict)

    return planned_hr_data_list


def get_evaluation_scores_comment(actual_session, session_scores_tt):
    pss_score_comment = ""
    duration_score_comment = ""
    sqs_session_score_comment = ""
    if actual_session:
        session_score = actual_session.session_score
        for score in session_scores_tt:
            if (
                score.score_range_lower_bound
                <= int(session_score.pss_score)
                <= score.score_range_upper_bound
            ):
                pss_score_comment = score.score_category
            if (
                score.score_range_lower_bound
                <= int(session_score.duration_score)
                <= score.score_range_upper_bound
            ):
                duration_score_comment = score.score_category
            if (
                score.score_range_lower_bound
                <= int(session_score.sqs_session_score)
                <= score.score_range_upper_bound
            ):
                sqs_session_score_comment = score.score_category

    return {
        "pss_score_comment": pss_score_comment,
        "duration_score_comment": duration_score_comment,
        "sqs_session_score_comment": sqs_session_score_comment,
    }


def get_accuracy_scores_comment(actual_session, session_scores_tt):
    duration_score_comment = ""
    intensity_score_comment = ""
    key_zone_score_comment = ""
    non_key_zone_score_comment = ""

    if actual_session:
        session_score = actual_session.session_score
        for score in session_scores_tt:
            lower_bound = score.score_range_lower_bound * 10
            upper_bound = score.score_range_upper_bound * 10

            if lower_bound <= int(session_score.duration_accuracy_score) <= upper_bound:
                duration_score_comment = score.score_category
            if (
                lower_bound
                <= int(session_score.intensity_accuracy_score)
                <= upper_bound
            ):
                intensity_score_comment = score.score_category
            if lower_bound <= int(session_score.key_zone_score) <= upper_bound:
                key_zone_score_comment = score.score_category
            if lower_bound <= int(session_score.non_key_zone_score) <= upper_bound:
                non_key_zone_score_comment = score.score_category

    return {
        "duration_score_comment": duration_score_comment,
        "intensity_score_comment": intensity_score_comment,
        "key_zone_score_comment": key_zone_score_comment,
        "non_key_zone_score_comment": non_key_zone_score_comment,
    }


def check_recovery_day(day_zone_focus):
    if day_zone_focus == 0:
        return True
    return False


def set_session_intensity_from_power(third_party_data, session, cur_ftp):
    intensity_service = IntensityService(
        weighted_power=third_party_data.weighted_power,
        ftp=cur_ftp,
        average_power=third_party_data.average_power,
    )
    session.actual_intensity = intensity_service.get_intensity_from_power()
    return session


def set_session_intensity_from_hr(third_party_data, session, cur_fthr):
    if third_party_data.moving_time:
        average_heart_rate = third_party_data.average_heart_rate
    elif third_party_data.elapsed_time:
        average_heart_rate = (
            third_party_data.total_heart_rate / third_party_data.elapsed_time
        )
    else:
        average_heart_rate = 0
    intensity_service = IntensityService(
        average_heart_rate=average_heart_rate, fthr=cur_fthr
    )
    session.actual_intensity = intensity_service.get_intensity_from_heart_rate()
    return session


def set_session_intensity(session, third_party_data, cur_ftp, cur_fthr):
    """
    Calculates session intensity given power or heart rate data.
    If power data is given, weighted power is also stored.
    """
    if (third_party_data.total_power or third_party_data.average_power) and cur_ftp:
        session = set_session_intensity_from_power(third_party_data, session, cur_ftp)
        return session

    if third_party_data.total_heart_rate or third_party_data.average_heart_rate:
        if not cur_fthr:
            session_date_time = session.session_date_time
            cur_max_hr = get_user_max_heart_rate(session.user_auth, session_date_time)
            cur_fthr = get_fthr_from_max_heart_rate(cur_max_hr)
        if cur_fthr:
            session = set_session_intensity_from_hr(third_party_data, session, cur_fthr)
            return session
    logger.info(f"Intensity calculation failed. FTP: {cur_ftp}, FTHR: {cur_fthr}")
    session.actual_intensity = 0
    return session


def set_session_pss(session):
    pss_service = PssService(session.actual_intensity, session.actual_duration / 60)
    pss = pss_service.get_pss()
    session.actual_pss = pss
    return session


def get_previous_sessions_pss(actual_session):
    """
    Following query will skip all the sessions after start time and return summation of all the previous sessions' pss
    """
    start_time = actual_session.session_date_time - timedelta(minutes=2)

    actual_sessions = (
        ActualSession.objects.filter_actual_sessions(user_auth=actual_session.user_auth)
        .filter(session_date_time__date=actual_session.session_date_time.date())
        .exclude(session_date_time__gt=start_time)
    )

    return sum(actual_session.actual_pss for actual_session in actual_sessions)


def set_session_load_acute_load(
    session,
    previous_sessions_pss,
    previous_load,
    previous_acute_load,
    is_onboarding_day,
):
    total_pss = session.actual_pss + previous_sessions_pss

    load_service = LoadService(previous_load, total_pss)
    load_today = load_service.get_load_today(is_onboarding_day)

    acute_load_service = AcuteLoadService(previous_acute_load, total_pss)
    acute_load_today = acute_load_service.get_acute_load_today(is_onboarding_day)

    session.actual_load = load_today
    session.actual_acute_load = acute_load_today
    return session


def set_session_sqs_session(actual_session, session_score):
    if not actual_session.session_code:
        session_score.sqs_session_score = 1
    else:
        planned_session = actual_session.planned_session
        abs_diff_intensity_service = AbsoluteDifferenceIntensityService(
            planned_session.planned_intensity, actual_session.actual_intensity
        )
        abs_diff_intensity = (
            abs_diff_intensity_service.get_absolute_difference_intensity()
        )

        sqs_session_service = SQSSessionService(abs_diff_intensity)
        session_score.sqs_session_score = sqs_session_service.get_sqs_session()

    return session_score


def set_session_sqs_today_score(session_score, previous_sqs_today, zone_focus):
    sqs_today_service = SqsTodayService(
        previous_sqs_today, session_score.sqs_session_score
    )
    sqs_today = sqs_today_service.get_sqs_today(zone_focus)
    session_score.sqs_today_score = sqs_today
    return session_score


def set_session_prs(actual_session, session_score):
    w_sqs_service = WeightingSqsService(session_score.sqs_today_score)
    w_sqs = w_sqs_service.get_weighting_sqs()

    recovery_index = get_obj_recovery_index(actual_session)

    prs_score_service = PrsService(actual_session.actual_load, recovery_index, w_sqs)
    prs_score = prs_score_service.get_prs()

    session_score.prs_score = prs_score
    return session_score


def set_session_status(actual_session, day_zone_focus):
    if check_recovery_day(day_zone_focus):
        session_status = "recovery"
    elif not actual_session.session_code:
        session_status = "unplanned"
    else:
        session_status = "planned"

    return session_status


def calculate_evaluation_scores(actual_session, session_score):
    planned_session = actual_session.planned_session

    abs_diff_duration_service = AbsoluteDifferenceDurationService(
        planned_session.planned_duration, actual_session.actual_duration
    )
    abs_diff_duration = abs_diff_duration_service.get_absolute_difference_duration()

    duration_score_service = DurationScoreService(abs_diff_duration)
    duration_score = duration_score_service.get_duration_score()

    session_score.duration_score = duration_score

    abs_diff_pss_service = AbsoluteDifferencePssService(
        planned_session.planned_pss, actual_session.actual_pss
    )
    abs_diff_pss = abs_diff_pss_service.get_absolute_difference_pss()

    pss_score_service = PssScoreService(abs_diff_pss)
    pss_score = pss_score_service.get_pss_score()

    session_score.pss_score = pss_score

    return session_score


def set_evaluation_scores(actual_session, session_score, session_status):
    # An unplanned session that's been done on recovery day
    if session_status == "recovery":
        session_score.duration_score = 1
        session_score.pss_score = 1
    # An unplanned session that's been done on non-recovery day
    elif session_status == "unplanned":
        session_score.duration_score = 3
        session_score.pss_score = 3
    else:
        session_score = calculate_evaluation_scores(actual_session, session_score)

    session_overall_score_service = SessionOverallScoreService(
        session_score.duration_score,
        session_score.pss_score,
        session_score.sqs_session_score,
    )
    session_score.overall_score = (
        session_overall_score_service.get_session_overall_score()
    )
    return session_score


def add_time_in_zones(result_time_in_zone, time_in_zones):
    for index, zone_data in enumerate(time_in_zones):
        result_time_in_zone[index]["value"] += zone_data["value"]
    return result_time_in_zone


def get_total_time_spent_in_zones(time_in_zones):
    time_spent = 0
    for zone_data in time_in_zones:
        time_spent += zone_data["value"]
    return time_spent


def get_time_spent_in_zones(time_in_zones, key_zones):
    time_spent_in_key_zones = 0
    time_spent_in_non_key_zones = 0
    for zone_data in time_in_zones:
        if zone_data["zone"] in key_zones:
            time_spent_in_key_zones += zone_data["value"]
        else:
            time_spent_in_non_key_zones += zone_data["value"]

    return Decimal(time_spent_in_key_zones), Decimal(time_spent_in_non_key_zones)


def is_time_spent_in_zone(time_in_zones):
    for zone_data in time_in_zones:
        if zone_data["value"]:
            return True
    return False


def set_zone_accuracy_scores(actual_session, planned_session, session_score):
    if actual_session.athlete_activity_code is None:
        return session_score

    athlete_activity = dakghor_get_athlete_activity(
        actual_session.athlete_activity_code
    ).json()["data"]["athlete_activity"]
    actual_time_in_power_zone = json.loads(athlete_activity["time_in_power_zone"])
    actual_time_in_heart_rate_zone = json.loads(
        athlete_activity["time_in_heart_rate_zone"]
    )

    user_auth = actual_session.user_auth
    activity_start_time = actual_session.session_date_time
    if get_user_ftp(user_auth, activity_start_time) and is_time_spent_in_zone(
        actual_time_in_power_zone
    ):
        actual_time_in_zone = actual_time_in_power_zone
        planned_time_in_zone = json.loads(planned_session.planned_time_in_power_zone)
    elif get_user_fthr(user_auth, activity_start_time) and is_time_spent_in_zone(
        actual_time_in_heart_rate_zone
    ):
        actual_time_in_zone = actual_time_in_heart_rate_zone
        planned_time_in_zone = json.loads(planned_session.planned_time_in_hr_zone)
    else:
        return session_score

    key_zones = json.loads(planned_session.session.key_zones)
    actual_time_in_key_zones, actual_time_in_non_key_zones = get_time_spent_in_zones(
        actual_time_in_zone, key_zones
    )
    planned_time_in_key_zones, planned_time_in_non_key_zones = get_time_spent_in_zones(
        planned_time_in_zone, key_zones
    )

    session_score.key_zone_score = SASService.calculate_accuracy_score(
        actual_value=actual_time_in_key_zones, planned_value=planned_time_in_key_zones
    )
    session_score.non_key_zone_score = SASService.calculate_accuracy_score(
        actual_value=actual_time_in_non_key_zones,
        planned_value=planned_time_in_non_key_zones,
    )

    session_score.key_zone_performance = SASService.calculate_key_zone_performance(
        actual_time_in_key_zones=actual_time_in_key_zones,
        planned_time_in_key_zones=planned_time_in_key_zones,
    )

    return session_score


def set_accuracy_scores(
    actual_session, planned_session, session_score, previous_sas_today
):
    session_score.duration_accuracy_score = SASService.calculate_accuracy_score(
        actual_session.actual_duration, planned_session.planned_duration
    )

    if actual_session.actual_intensity:
        session_score.intensity_accuracy_score = SASService.calculate_accuracy_score(
            actual_session.actual_intensity, planned_session.planned_intensity
        )

    session_score = set_zone_accuracy_scores(
        actual_session, planned_session, session_score
    )
    session_score.set_overall_accuracy_score()

    session_score.sas_today_score = SASService.calculate_sas_today(
        previous_sas_today,
        session_score.overall_accuracy_score,
        planned_session.zone_focus,
    )

    weighting_sas = SASService.calculate_weighting_sas(session_score.sas_today_score)
    recovery_index = get_obj_recovery_index(actual_session)
    prs_score_service = PrsService(
        actual_session.actual_load, recovery_index, weighting_sas
    )
    session_score.prs_accuracy_score = prs_score_service.get_prs()
    return session_score


def set_session_scores(
    actual_session, planned_session, previous_sqs_today, previous_sas_today
):
    session_score = SessionScore()

    session_score = set_session_sqs_session(actual_session, session_score)
    session_score = set_session_sqs_today_score(
        session_score, previous_sqs_today, planned_session.zone_focus
    )
    session_score = set_session_prs(actual_session, session_score)

    session_status = set_session_status(actual_session, planned_session.zone_focus)
    session_score = set_evaluation_scores(actual_session, session_score, session_status)
    session_score = set_accuracy_scores(
        actual_session, planned_session, session_score, previous_sas_today
    )
    session_score.save()

    actual_session.session_score = session_score
    return actual_session


def calculate_session(
    user_auth,
    user_ftp,
    user_fthr,
    activity_datetime,
    utc_activity_datetime,
    third_party_data,
    actual_session=None,
):
    actual_yesterday, is_onboarding_day = get_actual_day_yesterday(
        user_auth, activity_datetime.date()
    )
    planned_day = PlannedDay.objects.filter(
        user_auth=user_auth, activity_date=activity_datetime.date(), is_active=True
    ).last()

    if actual_session is None:
        actual_session = create_actual_session(
            planned_day, activity_datetime, utc_activity_datetime, user_auth
        )
        actual_session.code = uuid.uuid4()

    if third_party_data.moving_time:
        actual_session.actual_duration = Decimal(
            third_party_data.moving_time / 60
        )  # Converting sec into min
    else:
        actual_session.actual_duration = Decimal(third_party_data.elapsed_time / 60)
    actual_session.actual_distance_in_meters = Decimal(third_party_data.distance)

    actual_session = set_session_intensity(
        actual_session, third_party_data, user_ftp, user_fthr
    )
    actual_session = set_session_pss(actual_session)

    previous_sessions_pss = get_previous_sessions_pss(actual_session)
    actual_session = set_session_load_acute_load(
        actual_session,
        previous_sessions_pss,
        actual_yesterday.actual_load,
        actual_yesterday.actual_acute_load,
        is_onboarding_day,
    )

    return actual_session, planned_day, actual_yesterday


def recalculate_sessions(user_auth, actual_day, actual_sessions):
    logger.info(f"Inside recalculate_session for day: {actual_day.id}")

    try:
        recovery_session = PlannedSession.objects.get(
            user_auth=user_auth,
            is_active=True,
            zone_focus=0,
            session_date_time__date=actual_day.activity_date,
        )
    except PlannedSession.DoesNotExist:
        recovery_session = None

    if not actual_sessions:
        return

    day_yesterday, is_onboarding_day = get_actual_day_yesterday(
        user_auth, actual_day.activity_date
    )

    user_sessions = []
    for actual_session in actual_sessions:
        if (
            recovery_session
            and actual_session.session_code == recovery_session.session_code
        ):
            # Skipping recovery session
            continue

        logger.info(f"Recalculating session {actual_session.id}")
        actual_session = create_new_model_instance(actual_session)

        previous_sessions_pss = get_previous_sessions_pss(actual_session)
        actual_session = set_session_load_acute_load(
            actual_session,
            previous_sessions_pss,
            day_yesterday.actual_load,
            day_yesterday.actual_acute_load,
            is_onboarding_day,
        )
        if actual_session.session_code is not None:
            planned_session = (
                PlannedSession.objects.filter(
                    session_code=actual_session.session_code, is_active=True
                )
                .select_related("session")
                .first()
            )
            actual_session = set_session_scores(
                actual_session,
                planned_session,
                day_yesterday.sqs_today,
                day_yesterday.sas_today,
            )

        if actual_session.activity_type == ActivityTypeEnum.CYCLING.value[1]:
            day_data_obj = set_actual_day_data(actual_session=actual_session)
            if day_data_obj:
                if day_data_obj.id:
                    day_data_obj = create_new_model_instance(day_data_obj)
                day_data_obj.reason = "Recalculate sessions"
                day_data_obj.save()
        actual_session.reason = "Recalculate sessions"
        user_sessions.append(actual_session)

    ActualSession.objects.bulk_create(user_sessions)

    logger.info("Bulk created sessions, exiting recalculate_sessions")


def recalculate_session_outside_plan(user_auth, actual_session):
    day_yesterday, is_onboarding_day = get_actual_day_yesterday(
        user_auth, actual_session.session_date_time.date()
    )
    actual_session = create_new_model_instance(actual_session)
    previous_sessions_pss = get_previous_sessions_pss(actual_session)
    actual_session = set_session_load_acute_load(
        actual_session,
        previous_sessions_pss,
        day_yesterday.actual_load,
        day_yesterday.actual_acute_load,
        is_onboarding_day,
    )
    actual_session.save()

    actual_day = ActualDay.objects.filter(
        user_auth=user_auth,
        is_active=True,
        activity_date=actual_session.session_date_time,
    ).first()
    actual_day.actual_load = actual_session.actual_load
    actual_day.actual_acute_load = actual_session.actual_acute_load
    actual_day.recovery_index = get_obj_recovery_index(actual_day)
    actual_today = create_new_model_instance(actual_day)
    actual_today.save()


def get_activity_info(actual_session, athlete_activity, user_personalise_data):
    is_uploaded_activity = bool(
        actual_session.third_party.code != ThirdPartySources.MANUAL.value[0]
    )

    if athlete_activity is None and is_uploaded_activity:
        weighted_power = (
            pss
        ) = (
            intensity
        ) = average_speed = elapsed_time = moving_time = distance = elevation = None

    elif is_uploaded_activity:
        pss = round(actual_session.actual_pss)
        intensity = int(actual_session.actual_intensity * 100)

        average_speed = None
        ride_summary = get_ride_summary(athlete_activity["ride_summary"])
        for summary in ride_summary:
            if summary["type"] == "Speed" and summary["average"] is not None:
                average_speed = round(summary["average"], 1)

        weighted_power = None
        if athlete_activity["weighted_power"] and user_personalise_data.current_ftp:
            weighted_power = round(athlete_activity["weighted_power"])

        elapsed_time = athlete_activity["elapsed_time"]
        moving_time = athlete_activity["moving_time"]
        distance = 0.0
        if athlete_activity["ride_summary"]:
            for data in athlete_activity["ride_summary"]:
                if data["type"] == "distance":
                    distance = round(data["total_value"] / 1000, 1)
                    break

        elevation = (
            round(actual_session.elevation_gain)
            if actual_session.elevation_gain
            else None
        )

    else:
        pillar_data = actual_session.pillar_data
        moving_time = pillar_data.moving_time_in_seconds
        elapsed_time = pillar_data.moving_time_in_seconds
        distance = round(pillar_data.total_distance_in_meter / 1000, 1)
        average_speed = round(pillar_data.average_speed, 1)
        elevation = None
        pss = round(actual_session.actual_pss)
        intensity = int(actual_session.actual_intensity * 100)
        weighted_power = None

    return get_session_info_dict(
        moving_time,
        elapsed_time,
        distance,
        average_speed,
        elevation,
        intensity,
        pss,
        weighted_power,
    )


def get_manual_activity_ride_summary(pillar_data):
    return [
        {
            "type": "Heart Rate",
            "unit": "bpm",
            "average": pillar_data.average_heart_rate,
        },
        {
            "type": "Speed",
            "unit": "km/h",
            "average": round(pillar_data.average_speed, 1),
        },
        {"type": "Power", "unit": "W", "average": pillar_data.average_power},
    ]


def check_overtraining(actual_session, day_yesterday, planned_day, user):
    """Checks if current session has breached any of the overtraining conditions and creates notification if it does"""

    logger.info(f"Overtraining check starts for user ID: {user.id}")

    if actual_session.actual_intensity > MAX_REPEATED_INTENSITY:
        yesterday_high_intensity_sessions = ActualSession.objects.filter(
            user_auth=user,
            session_date_time__date=day_yesterday.activity_date,
            is_active=True,
            actual_intensity__gt=MAX_REPEATED_INTENSITY,
        ).exists()
        if yesterday_high_intensity_sessions:
            notification_type_enum = (
                NotificationTypeEnum.CONSECUTIVE_HIGH_INTENSITY_SESSIONS
            )
            create_notification(
                user,
                notification_type_enum,
                OVERTRAINING_NOTIFICATION_TITLE,
                OVERTRAINING_NOTIFICATION_BODY,
                actual_session.code,
            )
            logger.info("CONSECUTIVE_HIGH_INTENSITY_SESSIONS warning triggered")

    single_ride_max_pss = (
        Decimal(MAX_SINGLE_RIDE_MULTIPLIER) * day_yesterday.actual_load
        - planned_day.commute_pss_day
    )
    load_constant = get_load_constant()
    acute_load_constant = get_acute_load_constant()
    pss_minimum_freshness = (
        (
            MINIMUM_FRESHNESS
            - (load_constant * day_yesterday.actual_load)
            + (acute_load_constant * day_yesterday.actual_acute_load)
        )
        / (acute_load_constant - load_constant)
    ) - planned_day.commute_pss_day

    if actual_session.actual_pss > single_ride_max_pss:
        notification_type_enum = NotificationTypeEnum.HIGH_SINGLE_RIDE_LOAD
        create_notification(
            user,
            notification_type_enum,
            OVERTRAINING_NOTIFICATION_TITLE,
            OVERTRAINING_NOTIFICATION_BODY,
            actual_session.code,
        )
        logger.info("HIGH_SINGLE_RIDE_LOAD warning triggered")
    if actual_session.actual_pss > pss_minimum_freshness:
        notification_type_enum = NotificationTypeEnum.HIGH_RECENT_TRAINING_LOAD
        create_notification(
            user,
            notification_type_enum,
            OVERTRAINING_NOTIFICATION_TITLE,
            OVERTRAINING_NOTIFICATION_BODY,
            actual_session.code,
        )
        logger.info("HIGH_RECENT_TRAINING_LOAD warning triggered")

    logger.info("Overtraining check ends")
