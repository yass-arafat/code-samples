import logging
import uuid
from copy import deepcopy
from datetime import datetime, timedelta

from django.db import transaction

from core.apps.activities.services import ReevaluationService
from core.apps.activities.utils import dakghor_get_athlete_activity
from core.apps.common.common_functions import (
    get_actual_day_yesterday,
    get_date_from_datetime,
)
from core.apps.common.enums.date_time_format_enum import DateTimeFormatEnum
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.tp_common_utils import get_third_party_instance
from core.apps.common.utils import (
    create_new_model_instance,
    get_max_heart_rate_from_age,
    log_extra_fields,
    update_is_active_value,
)
from core.apps.daily.models import UserDay
from core.apps.evaluation.daily_evaluation.utils import set_actual_day_data
from core.apps.evaluation.session_evaluation.utils import (
    get_actual_session,
    set_session_scores,
)
from core.apps.garmin.models import CurveCalculationData
from core.apps.plan.enums.session_status_enum import (
    SessionLabelTypeEnum,
    SessionStatusEnum,
)
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.utils import (
    get_user_fthr,
    get_user_ftp,
    get_user_max_heart_rate,
)

from ..common.services import RoundServices
from ..user_profile.services import ZoneDifficultyLevelService
from .enums.session_pairing_message_enum import SessionPairingMessage
from .models import ActualSession, PlannedSession, UserAway, UserAwayInterval
from .sets_and_reps_dictionary import sets_and_reps_dict
from .tasks import populate_compressed_power_hr_data
from .utils import (
    get_actual_session_interval_data,
    get_planned_session_interval_data,
    get_session_metadata,
    get_session_name,
    populate_planned_time_in_hr_zone,
    set_actual_session,
    set_garmin_data,
    set_planned_session,
    update_achievement_data,
)

logger = logging.getLogger(__name__)


class SessionService:
    @classmethod
    def delete_session(cls, current_session, user):
        """Deletes the actual session with actual id of user and re-evaluates day data fom that day until today"""
        from core.apps.activities.services import ReevaluationService

        update_achievement_data(user, current_session)

        session_date = current_session.session_date_time.date()
        # Updating is_active to false for all third_party activities with current session's session date time,
        # as they are the same session uploaded from different third parties
        actual_sessions = ActualSession.objects.filter(
            session_date_time=current_session.session_date_time,
            is_active=True,
            session_code__isnull=True,
        )
        update_is_active_value(actual_sessions, False, "Delete session")

        athlete_activity_codes = [
            actual_session.athlete_activity_code for actual_session in actual_sessions
        ]
        curve_data = CurveCalculationData.objects.filter(
            athlete_activity_code__in=athlete_activity_codes,
            user_auth=user,
            is_active=True,
        )
        update_is_active_value(curve_data, False)

        if session_date != user.user_local_date:
            user_plan = current_session.user_plan
            if user_plan:
                with transaction.atomic():
                    ReevaluationService.reevaluate_session_data_of_single_plan(
                        user, user_plan, session_date
                    )

    @classmethod
    def edit_session(
        cls,
        actual_id,
        user,
        activity_name,
        activity_label,
        description,
        effort_level,
        planned_id,
    ):
        actual_session = get_actual_session(user, actual_id)
        actual_session = create_new_model_instance(actual_session)
        user_event = cls.check_event_day(actual_session)
        if user_event:
            user_event.name = activity_name[:55]
            user_event.save(update_fields=["name", "updated_at"])
            logger.info(
                f"Edit goal name from {user_event.name} to {activity_name}. "
                f"User id: {user.id}"
            )
        else:
            actual_session.activity_name = activity_name
        if activity_label:
            actual_session.session_label = activity_label
        actual_session.description = description
        actual_session.effort_level = effort_level
        actual_session.reason = "Edit session"
        actual_session.save()
        logger.info(f"Actual session {actual_id} is edited. User id: {user.id}")
        session_metadata = get_session_metadata(
            actual_session=actual_session, planned_id=planned_id
        )

        return session_metadata

    @staticmethod
    def check_event_day(actual_session):
        if not (actual_session and actual_session.session_code):
            return None

        user_event = actual_session.user_plan.user_event
        event_start_date = user_event.start_date
        event_end_date = user_event.end_date
        session_date = actual_session.session_date_time.date()

        if event_start_date <= session_date <= event_end_date:
            return user_event


class PopulateService:
    @staticmethod
    def get_activity_type(user_auth, actual_session):
        if actual_session["strava_data__activity_type"]:
            return actual_session["strava_data__activity_type"]
        if actual_session["garmin_data__activity_type"]:
            return actual_session["garmin_data__activity_type"]
        if actual_session["pillar_data__activity_type"]:
            return actual_session["pillar_data__activity_type"]
        if actual_session["third_party__id"] is None:
            return "recovery"
        logger.error(
            "Failed to find activity type",
            extra=log_extra_fields(user_auth_id=user_auth.id),
        )
        return None

    @classmethod
    def session_planned_time_in_hr_zone_services(cls, user):
        sessions = user.planned_sessions.filter(is_active=True)
        for session in sessions:
            if session.name == "Unplanned":
                continue
            logger.info(f"Populating planned_time_in_hr_zone in session: {session.id}")
            populate_planned_time_in_hr_zone(session)
            logger.info(
                f"Completed populating planned_time_in_hr_zone in session: {session.id}"
            )

    @classmethod
    def set_activity_type_in_actual_session(cls, user_auth):
        value_fields = [
            "id",
            "strava_data__activity_type",
            "garmin_data__activity_type",
            "pillar_data__activity_type",
            "athlete_activity_code",
            "third_party__id",
        ]
        actual_sessions = ActualSession.objects.filter(
            user_auth=user_auth, activity_type__isnull=True
        ).values(*value_fields)
        for actual_session in actual_sessions:
            actual_session_obj = ActualSession.objects.filter(
                id=actual_session["id"]
            ).first()
            actual_session_obj.activity_type = cls.get_activity_type(
                user_auth, actual_session
            )
            actual_session_obj.save(update_fields=["activity_type"])

    @classmethod
    def set_actual_intervals(cls, user_auth):
        actual_sessions = ActualSession.objects.filter(
            user_auth=user_auth,
            athlete_activity_code__isnull=False,
            session_code__isnull=False,
            actual_intervals__isnull=True,
        )
        for actual_session in actual_sessions:
            actual_session = SessionIntervalService(
                user_auth, actual_session
            ).set_actual_intervals()
            if actual_session.actual_intervals:
                actual_session.save(update_fields=["actual_intervals"])

    @classmethod
    def set_compressed_power_hr_data(cls, user_auth):
        actual_sessions = (
            ActualSession.objects.filter(
                user_auth=user_auth, athlete_activity_code__isnull=False
            )
            .distinct("athlete_activity_code")
            .values("session_date_time", "athlete_activity_code")
        )
        for actual_session in actual_sessions:
            athlete_activity_code = str(actual_session["athlete_activity_code"])
            session_date_time = actual_session["session_date_time"].strftime(
                DateTimeFormatEnum.app_date_time_format.value
            )
            populate_compressed_power_hr_data.delay(
                user_auth.id, athlete_activity_code, session_date_time
            )


class MigrationService:
    @classmethod
    def migrate_day_and_session_data(cls, user):
        error = False
        try:
            user_days = UserDay.objects.filter(user_auth=user).order_by("activity_date")
            prev_date, day_code, prev_week_start_date, week_code = (
                None,
                None,
                None,
                None,
            )

            for user_day in user_days:

                user_week = user_day.user_week
                if user_week.start_date != prev_week_start_date:
                    week_code = uuid.uuid4()
                user_week.week_code = week_code
                user_day.week_code = week_code
                user_week.save()
                prev_week_start_date = user_week.start_date

                logger.info(f"starts migrating user day id {user_day.id}")
                if user_day.activity_date != prev_date:
                    day_code = uuid.uuid4()
                    prev_date = user_day.activity_date

                cls.migrate_session_data_and_set_day_code(
                    user_day=user_day, day_code=day_code
                )
                user_day.day_code = day_code
            logger.info("User day bulk update started")
            UserDay.objects.bulk_update(user_days, ["day_code", "week_code"])
            logger.info("User day bulk update Finished Succesfully")
        except Exception as e:
            logger.exception(str(e))
            error = True

        return error

    @classmethod
    def migrate_session_data_and_set_day_code(cls, user_day, day_code):
        user_sessions = user_day.user_sessions.all()
        for user_session in user_sessions:
            session_code = None
            logger.info(f"starts migrating user session {user_session.id}")
            if user_session.session:
                logger.info(
                    f"starts migrating planned data from user session {user_session.id}"
                )
                session_code = set_planned_session(
                    user_session=user_session, day_code=day_code
                )
            if user_session.garmin_data:
                logger.info(
                    f"starts migrating garmin data from user session {user_session.id}"
                )
                set_garmin_data(user_session=user_session)
                logger.info(
                    f"starts migrating actual session data from user session {user_session.id}"
                )
                set_actual_session(
                    user_session=user_session,
                    day_code=day_code,
                    session_code=session_code,
                )
            elif user_session.zone_focus == 0 and user_session.overall_score:
                logger.info(
                    f"starts migrating actual session data from user recovery session {user_session.id}"
                )
                set_actual_session(
                    user_session=user_session,
                    day_code=day_code,
                    session_code=session_code,
                )

    @classmethod
    def populate_actual_session_third_party_field(cls, user_auth):
        actual_sessions = ActualSession.objects.filter(user_auth=user_auth)
        for actual_session in actual_sessions:
            if actual_session.garmin_data:
                actual_session.third_party = get_third_party_instance(
                    ThirdPartySources.GARMIN.value[0]
                )
            elif actual_session.strava_data:
                actual_session.third_party = get_third_party_instance(
                    ThirdPartySources.STRAVA.value[0]
                )

            actual_session.save(update_fields=["third_party"])


class UserAwayService:
    def __init__(self, user, start_date, end_date):
        self.user = user
        self.start_date = get_date_from_datetime(
            datetime.strptime(start_date.split()[0], "%Y-%m-%d")
        )
        self.end_date = get_date_from_datetime(
            datetime.strptime(end_date.split()[0], "%Y-%m-%d")
        )

    def set_user_away(self, reason):
        user_away_list = []
        away_start_date = self.start_date
        self.handle_overlapping_intervals()
        away_interval = UserAwayInterval.objects.create(
            reason=reason,
            interval_code=uuid.uuid4(),
            start_date=self.start_date,
            end_date=self.end_date,
        )
        while away_start_date <= self.end_date:
            user_away = UserAway(
                user_auth=self.user,
                user_id=self.user.code,
                away_date=away_start_date,
                interval_code=away_interval.interval_code,
            )
            user_away_list.append(user_away)
            away_start_date = away_start_date + timedelta(days=1)
        UserAway.objects.bulk_create(user_away_list)

    def handle_overlapping_intervals(self):
        overlapping_away_days = UserAway.objects.filter(
            user_auth=self.user,
            is_active=True,
            away_date__gte=self.start_date,
            away_date__lte=self.end_date,
        )
        overlapping_interval_codes = []
        for overlapping_away_day in overlapping_away_days:
            overlapping_away_day.is_active = False
            if overlapping_away_day.interval_code not in overlapping_interval_codes:
                overlapping_interval_codes.append(overlapping_away_day.interval_code)
            overlapping_away_day.save()

        all_overlapping_intervals = UserAwayInterval.objects.filter(
            is_active=True, interval_code__in=overlapping_interval_codes
        )
        for overlapping_interval in all_overlapping_intervals:
            if (
                self.start_date <= overlapping_interval.start_date
                and self.end_date >= overlapping_interval.end_date
            ):
                overlapping_interval.is_active = False
            elif (
                self.start_date <= overlapping_interval.start_date
                and self.end_date < overlapping_interval.end_date
            ):
                overlapping_interval.is_active = False
                start_date = self.end_date + timedelta(days=1)
                self.create_away_interval(
                    overlapping_interval, start_date, overlapping_interval.end_date
                )
            elif (
                self.start_date > overlapping_interval.start_date
                and self.end_date >= overlapping_interval.end_date
            ):
                overlapping_interval.is_active = False
                end_date = self.start_date - timedelta(days=1)
                self.create_away_interval(
                    overlapping_interval, overlapping_interval.start_date, end_date
                )
            elif (
                self.start_date > overlapping_interval.start_date
                and self.end_date < overlapping_interval.end_date
            ):
                overlapping_interval.is_active = False
                end_date = self.start_date - timedelta(days=1)
                self.create_away_interval(
                    overlapping_interval, overlapping_interval.start_date, end_date
                )
                start_date = self.end_date + timedelta(days=1)
                away_interval = UserAwayInterval.objects.create(
                    reason=overlapping_interval.reason,
                    interval_code=uuid.uuid4(),
                    start_date=start_date,
                    end_date=overlapping_interval.end_date,
                )
                split_away_days = UserAway.objects.filter(
                    user_auth=self.user,
                    is_active=True,
                    away_date__range=(start_date, overlapping_interval.end_date),
                )
                user_away_list = []
                for split_away_day in split_away_days:
                    split_away_day.is_active = False
                    split_away_day.save()
                    user_away = UserAway(
                        user_auth=self.user,
                        user_id=self.user.code,
                        away_date=split_away_day.away_date,
                        interval_code=away_interval.interval_code,
                    )
                    user_away_list.append(user_away)
                UserAway.objects.bulk_create(user_away_list)
            overlapping_interval.save()

    def create_away_interval(self, overlapping_interval, start_date, end_date):
        away_interval = UserAwayInterval.objects.create(
            reason=overlapping_interval.reason,
            interval_code=overlapping_interval.interval_code,
            start_date=start_date,
            end_date=end_date,
        )
        return away_interval

    def is_valid_input(self):
        if not isinstance(self.user, UserAuthModel):
            return False, "No user found"

        if self.start_date > self.end_date:
            return False, "Start date may not be greater than end date"

        today = datetime.today().date()
        if self.start_date < today or self.end_date < today:
            return False, "You may not be away for past dates"

        user_active_plan = self.user.user_plans.filter(is_active=True).last()
        if not user_active_plan:
            return False, "You dont have any active plan"

        if (
            self.start_date > user_active_plan.end_date
            or self.end_date < user_active_plan.start_date
        ):
            return False, "Start date and end date should be within current plan"

        return True, ""


class UserAwayDeleteService:
    success_message = "User away has been deleted successfully"
    failure_message = "Could not delete user away. Error: "

    def __init__(self, user):
        self.user = user

    def delete(self, user_away_id):
        try:
            user_away = UserAway.objects.get(id=user_away_id)
            user_away.is_active = False
            user_away.save()
        except Exception as e:
            return False, self.failure_message + str(e)
        else:
            return True, self.success_message

    def delete_all(self, user_away_id):
        try:
            user_away = UserAway.objects.get(id=user_away_id)
            away_interval = UserAwayInterval.objects.filter(
                interval_code=user_away.interval_code, is_active=True
            ).last()
            user_away_objects = UserAway.objects.filter(
                user_auth=self.user,
                away_date__range=(away_interval.start_date, away_interval.end_date),
            )
            update_is_active_value(user_away_objects, False)

        except Exception as e:
            return False, self.failure_message + str(e)
        else:
            return True, self.success_message


class SessionPairingService:
    @classmethod
    def pair_completed_session_with_planned_session(cls, actual_id, user):
        """Pairs the provided completed session with the planned session of that day and returns the new session
        metadata"""
        actual_session = get_actual_session(user, actual_id)
        planned_session = (
            PlannedSession.objects.filter(
                session_date_time__date=actual_session.session_date_time.date(),
                user_auth=user,
                is_active=True,
            )
            .select_related("session")
            .last()
        )
        session_code = planned_session.session_code

        if ActualSession.objects.filter(
            session_code=session_code, is_active=True, third_party__isnull=False
        ).exists():
            logger.error(f"Planned session id: {planned_session.id} is already paired.")
            return None
        else:
            is_event_session, planned_session_name = cls.pair_actual_session(
                planned_session, actual_session, session_code, user
            )

            actual_today = set_actual_day_data(actual_session=actual_session)
            if actual_today:
                """
                If it's a completely new actual day, then there will be no created_at and updated_at
                and we should not make is_active=false and insert new row. we will just save a new actual day instance
                """
                if actual_today.created_at:
                    actual_today = create_new_model_instance(actual_today)
                    actual_today.reason = "Pairing session"
                actual_today.save()

                current_date = actual_session.session_date_time.date()
                if current_date != user.user_local_date:
                    date_from = current_date + timedelta(days=1)
                    user_plan = actual_session.user_plan
                    if user_plan:
                        ReevaluationService.reevaluate_session_data_of_single_plan(
                            user, user_plan, date_from
                        )

            actual_session_name = get_session_name(
                actual_session,
                None,
                actual_session.session_date_time,
                activity_type=actual_session.activity_type,
            )
            pairing_successful_message = (
                SessionPairingMessage.get_pairing_successful_message(
                    actual_session_name, planned_session_name, is_event_session
                )
            )

            logger.info(
                f"Actual session {actual_id} is paired with planned session {planned_session.id} "
                f"by user id: {user.id}"
            )

            return {
                "actual_id": actual_session.pk,
                "planned_id": planned_session.id,
                "activity_type": actual_session.activity_type,
                "session_status": SessionStatusEnum.PAIRED,
                "pairing_successful_message": pairing_successful_message,
            }

    @classmethod
    def unpair_evaluated_session_from_planned_session(cls, actual_id, user):
        """Unpairs the provided evaluated session from that day's planned session
        and returns the new session metadata"""

        actual_session = get_actual_session(user, actual_id)
        session_score = actual_session.session_score
        if not (actual_session or session_score):
            logger.error(
                f"No actual session or session score was found. Actual session id: {actual_id}"
            )
            return None
        cls.unpair_actual_session(actual_session)

        current_date = actual_session.session_date_time.date()
        if current_date != user.user_local_date:
            date_from = current_date
            user_plan = actual_session.user_plan
            if user_plan:
                ReevaluationService.reevaluate_session_data_of_single_plan(
                    user, user_plan, date_from
                )

        logger.info(
            f"Actual session {actual_id} is unpaired from planned session. User id: {user.id}"
        )

        return {
            "actual_id": actual_session.pk,
            "planned_id": None,
            "activity_type": actual_session.activity_type,
            "session_status": SessionStatusEnum.UNPAIRED,
        }

    @staticmethod
    def pair_actual_session(planned_session, actual_session, session_code, user):
        logger.info("pair_actual_session function is called")
        user_plan = actual_session.user_plan
        event_date = user_plan.end_date if user_plan.user_event else None
        if not actual_session or (
            planned_session.is_recovery_session()
            and event_date != actual_session.session_date_time.date()
        ):
            return None

        day_yesterday, _ = get_actual_day_yesterday(
            user, actual_session.session_date_time.date()
        )
        actual_session = create_new_model_instance(actual_session)
        actual_session.session_code = session_code
        actual_session.show_pairing_message = False
        if event_date == actual_session.session_date_time.date():
            actual_session.session_label = SessionLabelTypeEnum.EVENT
            is_event_session = True
            planned_session_name = user_plan.user_event.name
        else:
            if actual_session.athlete_activity_code:
                SessionIntervalService(
                    user, actual_session, planned_session
                ).set_actual_intervals()
            set_session_scores(
                actual_session,
                planned_session,
                day_yesterday.sqs_today,
                day_yesterday.sas_today,
            )
            is_event_session = False
            planned_session_name = planned_session.name

        actual_session.reason = "Pairing session"
        actual_session.save()
        logger.info("pair_actual_session function ended")

        ZoneDifficultyLevelService.update_zone_difficulty_level(user, planned_session)

        return is_event_session, planned_session_name

    @staticmethod
    def unpair_actual_session(actual_session):
        logger.info("unpair_actual_session function is called")

        event_date = actual_session.user_plan.end_date
        actual_session = create_new_model_instance(actual_session)
        actual_session.session_score = None
        actual_session.session_code = None
        actual_session.actual_intervals = None
        if event_date == actual_session.session_date_time.date():
            actual_session.session_label = SessionLabelTypeEnum.TRAINING_SESSION

        actual_session.reason = "Unpairing session"
        actual_session.save()
        logger.info("unpair_actual_session function ended")


class SessionIntervalService:
    def __init__(self, user_auth, actual_session, planned_session=None):
        self.user_auth = user_auth
        self.actual_session = actual_session
        self.planned_session = (
            planned_session
            or PlannedSession.objects.filter(
                session_code=self.actual_session.session_code, is_active=True
            ).last()
        )
        self.athlete_activity = dakghor_get_athlete_activity(
            self.actual_session.athlete_activity_code
        ).json()["data"]["athlete_activity"]

        self.user_ftp = get_user_ftp(
            self.user_auth, self.actual_session.session_date_time
        )
        self.user_fthr = get_user_fthr(
            self.user_auth, self.actual_session.session_date_time
        )
        self.user_max_heart_heart = get_user_max_heart_rate(
            self.user_auth, self.actual_session.session_date_time
        )

    def set_actual_intervals(self):
        planned_interval_data = get_planned_session_interval_data(
            self.planned_session,
            self.user_ftp,
            self.user_fthr,
            self.user_max_heart_heart,
        )
        actual_interval_data = get_actual_session_interval_data(
            planned_interval_data, self.athlete_activity
        )
        if actual_interval_data:
            self.actual_session.actual_intervals = actual_interval_data
        return self.actual_session


class SetsAndRepsService:
    def __init__(self, user, session_code, pad_time_in_seconds):
        self.session_dict = deepcopy(sets_and_reps_dict[session_code])
        self.pad_time = round(pad_time_in_seconds / 60)
        self.session_dict_length = len(self.session_dict)
        self.user_personalise_data = user.personalise_data.filter(is_active=True).last()
        self.user_ftp = self.user_personalise_data.current_ftp
        self.user_fthr = self.user_personalise_data.current_fthr
        self.user_max_heart_rate = self.user_personalise_data.max_heart_rate
        if not self.user_max_heart_rate:
            self.user_max_heart_rate = get_max_heart_rate_from_age(
                self.user_personalise_data.date_of_birth
            )

    # TODO: Need to refactor below methods, specially to increase readability
    def get_session_sets_and_reps(self):
        for set_index in range(self.session_dict_length):
            current_set = self.session_dict[set_index]
            set_values_length = len(current_set["values"])

            for value_index in range(set_values_length):
                value = current_set["values"][value_index]
                steps_length = len(value["steps"])
                step_index = 0

                while step_index < steps_length:
                    # If current step is a padding interval and pad_time == 0,
                    # then remove this pad interval step from session dict.
                    # If pad_time > 0, replace "{pad_time}" substring in the step string
                    # with the pad_time of current planned session
                    if "pad_time" in value["steps"][step_index]:
                        if not self.pad_time:
                            value["steps"].pop(step_index)
                            value["threshold_values"].pop(step_index)
                            # We have deleted one element from steps list
                            # So we need to decrease steps_length by 1
                            steps_length -= 1
                            continue
                        value["steps"][step_index] = value["steps"][step_index].replace(
                            "pad_time", str(self.pad_time)
                        )

                    step_count = value["step_count"][step_index]
                    threshold_values = value["threshold_values"]
                    boundaries = self.get_sets_and_reps_step_boundary(
                        step_count, threshold_values, step_index
                    )
                    calculated_step = value["steps"][step_index].format(*boundaries)
                    self.session_dict[set_index]["values"][value_index]["steps"][
                        step_index
                    ] = calculated_step

                    step_index += 1

        return self.session_dict

    def get_sets_and_reps_step_boundary(self, step_count, threshold_values, step_index):
        upper_boundaries = []
        lower_boundaries = []
        unit = ""

        for count in range(step_count):
            index = step_index + count
            if self.user_ftp:
                if isinstance(threshold_values[index]["ftp_lower"], str):
                    lower_power_boundary = threshold_values[index]["ftp_lower"]
                    upper_power_boundary = threshold_values[index]["ftp_upper"]
                else:
                    lower_power_boundary = RoundServices.round_power(
                        self.user_ftp * (threshold_values[index]["ftp_lower"] / 100)
                    )
                    upper_power_boundary = RoundServices.round_power(
                        self.user_ftp * (threshold_values[index]["ftp_upper"] / 100)
                    )
                lower_boundaries.append(lower_power_boundary)
                upper_boundaries.append(upper_power_boundary)
                unit = "w"

            elif self.user_fthr:
                if isinstance(threshold_values[index]["fthr_lower"], str):
                    lower_hr_boundary = threshold_values[index]["fthr_lower"]
                    upper_hr_boundary = threshold_values[index]["fthr_upper"]
                else:
                    lower_hr_boundary = RoundServices.round_heart_rate(
                        self.user_fthr * (threshold_values[index]["fthr_lower"] / 100)
                    )
                    upper_hr_boundary = RoundServices.round_heart_rate(
                        self.user_fthr * (threshold_values[index]["fthr_upper"] / 100)
                    )
                lower_boundaries.append(lower_hr_boundary)
                upper_boundaries.append(upper_hr_boundary)
                unit = "bpm"

            elif self.user_max_heart_rate:
                if isinstance(threshold_values[index]["mhr_lower"], str):
                    lower_hr_boundary = threshold_values[index]["mhr_lower"]
                    upper_hr_boundary = threshold_values[index]["mhr_upper"]
                else:
                    lower_hr_boundary = RoundServices.round_heart_rate(
                        self.user_max_heart_rate
                        * (threshold_values[index]["mhr_lower"] / 100)
                    )
                    upper_hr_boundary = RoundServices.round_heart_rate(
                        self.user_max_heart_rate
                        * (threshold_values[index]["mhr_upper"] / 100)
                    )
                lower_boundaries.append(lower_hr_boundary)
                upper_boundaries.append(upper_hr_boundary)
                unit = "bpm"

        boundary_list = []
        lower_boundary_length = len(lower_boundaries)
        for index in range(lower_boundary_length):
            lower_boundary = lower_boundaries[index]
            upper_boundary = upper_boundaries[index]

            if lower_boundary == upper_boundary:
                if isinstance(lower_boundary, str):
                    boundary_list.append(str(lower_boundary))
                    continue
                boundary_list.append(str(lower_boundary) + " " + unit)
            else:
                boundary_string = (
                    str(lower_boundary) + "-" + str(upper_boundary) + " " + unit
                )
                boundary_list.append(boundary_string)
        boundaries = tuple(
            boundary_list
        )  # Can not format string with list, we need tuple for that

        return boundaries
