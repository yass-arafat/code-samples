import calendar
import logging
import operator
from datetime import date, datetime, timedelta
from decimal import Decimal

from rest_framework.exceptions import ValidationError

from core.apps.block.models import UserBlock
from core.apps.calculations.evaluation.prs_services import PrsService
from core.apps.calculations.evaluation.sqs_services import WeightingSqsService
from core.apps.calculations.onboarding.load_start_calculations import (
    get_pss_week,
    get_starting_user_load,
)
from core.apps.calculations.onboarding.models.load_start_model import (
    LoadStartModel,
    PSSWeekModel,
)
from core.apps.common.common_functions import (
    format_timezone,
    get_timezone_offset_from_datetime_diff,
)
from core.apps.common.const import (
    FTHR_BOUNDARY,
    FTP_BOUNDARY,
    MAX_HR_BOUNDARY,
    MIN_STARTING_LOAD,
    MORNING_CRONJOB_TIME,
    USER_UTP_SETTINGS_QUEUE_PRIORITIES,
    UTC_TIMEZONE,
)
from core.apps.common.date_time_utils import (
    DateTimeUtils,
    convert_str_date_to_date_obj,
    convert_timezone_offset_to_seconds,
)
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.models import CronHistoryLog
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    create_new_model_instance,
    get_user_connected_table_instance,
    log_extra_fields,
    make_context,
)
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.daily.utils import get_rides_completed_and_total
from core.apps.evaluation.daily_evaluation.utils import day_morning_calculation
from core.apps.event.services import UserEventService
from core.apps.packages.models import UserPackage
from core.apps.packages.tasks import create_package_plan
from core.apps.plan.tasks import create_plan
from core.apps.session.models import ActualSession, PlannedSession
from core.apps.user_auth.models import UserAuthModel
from core.apps.utp.utils import update_utp_settings

from ..packages.utils import create_user_knowledge_hub_entries
from .avatar import get_avatar
from .dictionary import get_athletes_dict_for_coach_portal_dashboard
from .enums.gender_enum import GenderEnum
from .enums.user_unit_system_enum import UserUnitSystemEnum
from .models import (
    AvailableTrainingDurationsInHour,
    CommuteWeek,
    TimeZone,
    UserActivityLog,
    UserMetaData,
    UserPersonaliseData,
    UserProfile,
    UserTrainingAvailability,
    ZoneDifficultyLevel,
)
from .utils import split_user_name

calendar.setfirstweekday(calendar.MONDAY)
logger = logging.getLogger(__name__)


class UserInfoService:
    def __init__(self, request):
        self.request = request
        self.user_id = request.session["user_id"]

        self.is_personalise_data_fields_updated = False
        self.is_profile_data_fields_updated = False

    def update_user_info(self):
        self._update_user_personalise_data()
        self._update_user_profile_data()

    def _update_user_personalise_data(self):
        user_personalise_data = UserPersonaliseData.objects.filter(
            user_id=self.user_id, is_active=True
        ).last()
        if not user_personalise_data:
            raise ValueError("No active user personalise data found")

        self._update_user_weight(user_personalise_data)

        if self.is_personalise_data_fields_updated:
            user_personalise_data = create_new_model_instance(user_personalise_data)
            user_personalise_data.save()

    def _update_user_weight(self, user_personalise_data):
        weight = self.request.data.get("weight")
        if weight is None:
            return
        if not UserPersonaliseData.is_valid_weight(weight):
            raise ValidationError("Weight is not in acceptable range")

        user_personalise_data.weight = weight
        self.is_personalise_data_fields_updated = True

    def _update_user_profile_data(self):
        user_profile = UserProfile.objects.filter(
            user_id=self.user_id, is_active=True
        ).last()
        if not user_profile:
            raise ValueError("No active user profile data found")

        self._update_user_timezone(user_profile)

        if self.is_profile_data_fields_updated:
            user_profile = create_new_model_instance(user_profile)
            user_profile.save()

    def _update_user_timezone(self, user_profile: UserProfile):
        timezone_id = self.request.data.get("timezone_id")
        if timezone_id is None:
            return

        try:
            timezone = TimeZone.objects.get(id=timezone_id)
        except Exception as e:
            logger.exception(
                "Invalid Timezone ID",
                extra=log_extra_fields(
                    user_id=self.user_id,
                    service_type=ServiceType.API.value,
                    exception_message=str(e),
                ),
            )
            raise ValueError("Invalid Timezone ID")

        user_profile.timezone = timezone
        self.is_profile_data_fields_updated = True


class UserProfileService:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")

    def get_first_history_input_date(self):
        personalise_data = (
            UserPersonaliseData.objects.filter(
                user_id=self.user_id, training_hours_over_last_4_weeks__isnull=False
            )
            .order_by("created_at")
            .first()
        )
        return str(personalise_data.created_at.date()) if personalise_data else None

    @classmethod
    def save_user_profile_data(cls, request, user):
        name = request.data.get("profile_data").get("name") or ""
        name, surname = split_user_name(name)

        gender = request.data.get("profile_data").get("gender")
        if not gender:
            return None, "Missing gender information"
        for x in GenderEnum:
            if x.value[1].lower() == gender.lower():
                gender = x.value[0]
                break

        unit_system = request.data.get("profile_data").get("unit_system")
        if not unit_system:
            unit_system = "Metric"
        for x in UserUnitSystemEnum:
            if x.value[1].lower() == unit_system.lower():
                unit_system = x.value[0]
                break
        allow_notification = request.data.get("profile_data").get("allow_notification")
        if not allow_notification:
            allow_notification = False

        timezone_offset = format_timezone(
            request.data.get("profile_data").get("timezone_offset")
        )
        if not timezone_offset:
            timezone_offset = UTC_TIMEZONE
        timezone = TimeZone.objects.get_closest_timezone(timezone_offset)

        user_profile = UserProfile(
            name=name,
            surname=surname,
            gender=gender,
            unit_system=unit_system,
            allow_notification=allow_notification,
            timezone=timezone,
            user_auth=user,
            user_id=user.code,
        )
        user_profile.save()
        return user_profile, "Created user profile successfully"

    @classmethod
    def set_user_personalise_data(cls, request, user):
        personalise_data = request.data.get("personalise_data")
        date_of_birth = personalise_data.get("date_of_birth")
        date_of_birth = convert_str_date_to_date_obj(date_of_birth)
        if not date_of_birth:
            return None, "No valid date of birth found"

        # Deprecated from R7
        is_power_meter_available = (
            personalise_data.get("is_power_meter_available") or False
        )

        weight = personalise_data.get("weight") or 0.0
        training_hours_over_last_4_weeks = personalise_data.get(
            "training_hours_over_last_4_weeks"
        )
        starting_load = None
        starting_prs = None
        if training_hours_over_last_4_weeks is not None:
            if not isinstance(training_hours_over_last_4_weeks, list):
                training_hours_over_last_4_weeks = [
                    training_hours_over_last_4_weeks
                ] * 4
            starting_load = get_user_starting_load(training_hours_over_last_4_weeks)
            starting_prs = get_user_starting_prs(starting_load=starting_load)

        current_ftp = personalise_data.get("current_ftp") or 0
        current_ftp = round(current_ftp)
        current_fthr = personalise_data.get("current_threshold_heart_rate") or 0
        current_fthr = round(current_fthr)
        max_heart_rate = personalise_data.get("max_heart_rate") or 0
        max_heart_rate = round(max_heart_rate)

        if not (current_ftp or current_fthr):
            return None, "Please enter at least FTP or FTHR."
        if current_ftp and not (
            FTP_BOUNDARY["lowest"] <= current_ftp <= FTP_BOUNDARY["highest"]
        ):
            return None, "Please enter a viable FTP value. Accepted range is 30-500."
        if current_fthr and not (
            FTHR_BOUNDARY["lowest"] <= current_fthr <= FTHR_BOUNDARY["highest"]
        ):
            return None, "Please enter a viable FTHR value. Accepted range is 80-200."
        if max_heart_rate and not (
            MAX_HR_BOUNDARY["lowest"] <= max_heart_rate <= MAX_HR_BOUNDARY["highest"]
        ):
            return (
                None,
                "Please enter a viable Max Heart Rate value. Accepted range is 100-230.",
            )

        success_message = "User personalise data saved successfully"

        user_personalise_data = UserPersonaliseData.objects.filter(
            user_auth=user, is_active=True
        ).last()
        if user_personalise_data:
            if date_of_birth:
                user_personalise_data.date_of_birth = date_of_birth
            if weight:
                user_personalise_data.weight = weight
            if training_hours_over_last_4_weeks:
                user_personalise_data.training_hours_over_last_4_weeks = (
                    training_hours_over_last_4_weeks
                )
            if starting_load:
                user_personalise_data.starting_load = starting_load
                user_personalise_data.starting_acute_load = starting_load
            if starting_prs:
                user_personalise_data.starting_prs = starting_prs
            if current_ftp:
                user_personalise_data.current_ftp = current_ftp
            if current_fthr:
                user_personalise_data.current_fthr = current_fthr
            if max_heart_rate:
                user_personalise_data.max_heart_rate = max_heart_rate
            user_personalise_data = create_new_model_instance(user_personalise_data)
            return user_personalise_data, success_message

        request_data = {
            "date_of_birth": date_of_birth,
            "weight": weight,
            "training_hours_over_last_4_weeks": training_hours_over_last_4_weeks,
            "starting_load": starting_load,
            "starting_acute_load": starting_load,
            "starting_prs": starting_prs,
            "current_ftp": current_ftp,
            "current_fthr": current_fthr,
            "max_heart_rate": max_heart_rate,
            "user_auth": user,
            "user_id": user.code,
            # Deprecated from R7
            "is_power_meter_available": is_power_meter_available,
        }

        return UserPersonaliseData(**request_data), success_message

    @classmethod
    def save_user_personalise_data(cls, request, user):
        user_personalise_data, message = cls.set_user_personalise_data(request, user)
        if isinstance(user_personalise_data, UserPersonaliseData):
            user_personalise_data.save()
        return user_personalise_data, message

    @classmethod
    def create_commute_days(cls, commute_days):
        commute_week = CommuteWeek()
        commute_week.first_day = commute_days[0]
        commute_week.second_day = commute_days[1]
        commute_week.third_day = commute_days[2]
        commute_week.fourth_day = commute_days[3]
        commute_week.fifth_day = commute_days[4]
        commute_week.sixth_day = commute_days[5]
        commute_week.seventh_day = commute_days[6]
        commute_week.save()
        return commute_week

    @classmethod
    def create_available_training_durations(cls, available_durations):
        week_durations = AvailableTrainingDurationsInHour()
        week_durations.first_day_duration = available_durations[0]
        week_durations.second_day_duration = available_durations[1]
        week_durations.third_day_duration = available_durations[2]
        week_durations.fourth_day_duration = available_durations[3]
        week_durations.fifth_day_duration = available_durations[4]
        week_durations.sixth_day_duration = available_durations[5]
        week_durations.seventh_day_duration = available_durations[6]
        week_durations.save()
        return week_durations

    @staticmethod
    def get_update_availability_start_date(user, request_data):
        schedule_start_date = request_data.get("schedule_start_date", None)
        if not schedule_start_date:
            schedule_start_date = DateTimeUtils.get_user_local_date_from_utc(
                user.timezone_offset, datetime.now()
            )
        else:
            schedule_start_date = datetime.strptime(
                schedule_start_date.split()[0], "%Y-%m-%d"
            ).date()

        schedule_start_day_planned_session = user.planned_sessions.filter(
            session_date_time__date=schedule_start_date, is_active=True
        ).last()
        if not schedule_start_day_planned_session:
            return schedule_start_date

        query_dict = {
            "session_code": schedule_start_day_planned_session.session_code,
            "is_active": True,
        }
        schedule_start_day_actual_session = ActualSession.objects.filter(
            **query_dict
        ).first()
        if schedule_start_day_actual_session:
            return schedule_start_date + timedelta(days=1)
        return schedule_start_date

    @classmethod
    def set_user_schedule_data(cls, request, user, user_event=None):

        user_schedule_data = UserTrainingAvailability()
        request_data = request.data.get("schedule_data", None)
        user_schedule_data.user_auth = user
        user_schedule_data.user_id = user.code
        schedule_start_date = cls.get_update_availability_start_date(user, request_data)
        user_schedule_data.start_date = schedule_start_date
        schedule_end_date = request_data.get("schedule_end_date", None)
        if not schedule_end_date:
            if user_event:
                schedule_end_date = user_event.end_date
            else:
                user_event = user.user_events.filter(is_active=True).last()
                schedule_end_date = user_event.end_date if user_event else None
        else:
            schedule_end_date = datetime.strptime(
                schedule_end_date.split()[0], "%Y-%m-%d"
            ).date()
        user_schedule_data.end_date = schedule_end_date

        commute_to_work_by_bike = request_data.get("commute_to_work_by_bike")
        user_schedule_data.duration_single_commute_in_hours = (
            request_data.get("duration_single_commute") or 0.0
        )
        days_commute_by_bike_data = request_data.get("days_commute_by_bike")
        available_training_hours_per_day_outside_commuting_data = request_data.get(
            "available_training_hours_per_day_outside_commuting"
        )

        if not commute_to_work_by_bike:
            user_schedule_data.commute_to_work_by_bike = False
            if not days_commute_by_bike_data:
                days_commute_by_bike_data = [False] * 7
        else:
            user_schedule_data.commute_to_work_by_bike = commute_to_work_by_bike

        if not days_commute_by_bike_data:
            return None, "Please mention at which days user commutes by bike"

        if not available_training_hours_per_day_outside_commuting_data:
            return None, "Please mention available training hours per day basis"

        days_commute_by_bike = cls.create_commute_days(days_commute_by_bike_data)
        available_training_hours_per_day_outside_commuting = (
            cls.create_available_training_durations(
                available_training_hours_per_day_outside_commuting_data
            )
        )

        user_schedule_data.days_commute_by_bike = days_commute_by_bike
        user_schedule_data.available_training_hours_per_day_outside_commuting = (
            available_training_hours_per_day_outside_commuting
        )
        return user_schedule_data

    @classmethod
    def save_user_schedule_data(cls, request, user):
        user_schedule_data = cls.set_user_schedule_data(request, user)
        try:
            user_schedule_data.save()
            return user_schedule_data, "Scheduled data saved successfully"
        except Exception as e:
            return None, str(e) + "Couldn't save user schedule data"

    @staticmethod
    def save_personalise_data(request, user):
        try:
            personalise_data = request.data.get("personalise_data")

            ftp = personalise_data.get("current_ftp")
            threshold_heart_rate = personalise_data.get("current_threshold_heart_rate")
            max_heart_rate = personalise_data.get("max_heart_rate")

            user_personalise_data = user.personalise_data.filter(is_active=True).last()
            training_hours_over_last_4_weeks = personalise_data.get(
                "training_hours_over_last_4_weeks"
            )
            if training_hours_over_last_4_weeks is not None:
                starting_load = get_user_starting_load_v2(
                    training_hours_over_last_4_weeks
                )
                user_personalise_data.starting_load = starting_load
                user_personalise_data.starting_acute_load = starting_load
                user_personalise_data.training_hours_over_last_4_weeks = [
                    training_hours_over_last_4_weeks
                ] * 4
            if ftp is not None:
                user_personalise_data.current_ftp = ftp
            if threshold_heart_rate is not None:
                user_personalise_data.current_fthr = threshold_heart_rate
            if max_heart_rate is not None:
                user_personalise_data.max_heart_rate = max_heart_rate

            user_personalise_data.save()

        except Exception as e:
            return None, "Could not save personalise data, " + str(e)

        return user_personalise_data, "Saved user personalise data successfully"

    @classmethod
    def migrate_user_schedule_data_to_training_availability(cls, schedule_data, user):
        user_training_availability = UserTrainingAvailability()
        user_training_availability.user_auth = user
        user_training_availability.user_id = user.code
        user_first_block = UserBlock.objects.filter(
            user_auth=user, is_active=True
        ).first()
        user_last_block = UserBlock.objects.filter(
            user_auth=user, is_active=True
        ).last()
        user_training_availability.start_date = user_first_block.start_date
        user_training_availability.end_date = user_last_block.end_date
        user_training_availability.days_commute_by_bike = cls.create_commute_days(
            eval(schedule_data.days_commute_by_bike)
        )
        user_training_availability.available_training_hours_per_day_outside_commuting = cls.create_available_training_durations(
            eval(schedule_data.available_training_hours_per_day_outside_commuting)
        )

        try:
            user_training_availability.save()
        except Exception as e:
            print(
                "could not migrate schedule data for user: {0}, error: {1}".format(
                    user.email, str(e)
                )
            )
        else:
            print(
                "migrated schedule data for user: {0} successfully".format(user.email)
            )

    @classmethod
    def save_timezone_to_profile(cls, timezone_id, user_profile):
        timezone = TimeZone.objects.filter(id=timezone_id).first()
        user_profile.timezone = timezone
        try:
            user_profile = create_new_model_instance(user_profile)
            user_profile.save()
            error = False
            msg = "Timezone saved successfully"
        except Exception as e:
            msg = "Failed to save timezone"
            logger.exception(msg, log_extra_fields(exception_message=str(e)))
            error = True
            msg = "Couldn't save Timezone to user profile"
        return error, msg

    @classmethod
    def run_cron_for_timezone_change(cls, user, previous_timezone, current_timezone):
        previous_tz_in_sec = convert_timezone_offset_to_seconds(previous_timezone)
        cur_tz_in_sec = convert_timezone_offset_to_seconds(current_timezone)

        cron_logs = []
        if cur_tz_in_sec > previous_tz_in_sec:
            cron_run_date = (datetime.now() + timedelta(days=-1)).date()

            cron_code = CronHistoryLog.CronCode.MORNING_CALCULATION
            if check_cron_needed(
                cron_code,
                datetime.combine(date.today(), MORNING_CRONJOB_TIME),
                cur_tz_in_sec,
                previous_tz_in_sec,
            ):
                try:
                    day_morning_calculation(user, cron_run_date + timedelta(days=1))
                    cron_status = CronHistoryLog.StatusCode.SUCCESSFUL
                except Exception as e:
                    cron_status = CronHistoryLog.StatusCode.FAILED
                    logger.info(
                        "Morning calculations failed in timezone change" + str(e)
                    )
                cron_logs.append(
                    CronHistoryLog(
                        cron_code=cron_code,
                        user_auth=user,
                        user_id=user.code,
                        status=cron_status,
                    )
                )

            CronHistoryLog.objects.bulk_create(cron_logs)

    @classmethod
    def get_athletes_info(cls, athlete_ids):

        athletes = UserAuthModel.objects.filter(pk__in=athlete_ids, is_active=True)
        athletes_dict = []
        for user_auth in athletes:
            (
                user_auth,
                user_profile,
                user_personalise_data,
                user_event,
            ) = get_user_connected_table_instance(None, user_auth)
            actual_day_data = ActualDay.objects.filter(
                user_auth=user_auth, activity_date=date.today(), is_active=True
            ).first()

            rides_completed, rides_total = get_rides_completed_and_total(user_auth)

            days_due_of_event = (user_event.start_date.date() - date.today()).days

            profile_image = user_auth.profile_images.filter(is_active=True).first()
            if profile_image:
                is_placeholder_image = False
                profile_image_url = profile_image.avatar.url
            else:
                is_placeholder_image = True
                profile_image_url = get_avatar()

            athletes_dict.append(
                get_athletes_dict_for_coach_portal_dashboard(
                    user_auth.id,
                    user_profile,
                    user_personalise_data,
                    rides_completed,
                    rides_total,
                    days_due_of_event,
                    user_auth.get_profile_picture(),
                    actual_day_data,
                    is_placeholder_image,
                    profile_image_url,
                )
            )

        athletes_dict = sorted(athletes_dict, key=operator.itemgetter("full_name"))
        return athletes_dict


class ActivityLogsService:
    @classmethod
    def save_user_activity_logs(cls, activity_logs):
        UserActivityLog.objects.bulk_create(
            [UserActivityLog(**activity_log) for activity_log in activity_logs]
        )


def check_cron_needed(cron_code, cron_time_const, cur_tz_in_sec, previous_tz_in_sec):
    user_last_cron = CronHistoryLog.objects.filter(cron_code=cron_code).last()
    cur_datetime = datetime.now()
    if user_last_cron:
        cron_timestamp = user_last_cron.timestamp.replace(tzinfo=None)
        if cur_datetime - timedelta(hours=24) <= cron_timestamp <= cur_datetime:
            cron_tz_offset = get_timezone_offset_from_datetime_diff(
                cron_time_const - cron_timestamp
            )
            cron_tz_in_sec = convert_timezone_offset_to_seconds(cron_tz_offset)
            if cur_tz_in_sec > cron_tz_in_sec > previous_tz_in_sec:
                return True
    return False


def get_user_starting_load(last_four_week_hours):
    week1_hours = last_four_week_hours[0]
    week2_hours = last_four_week_hours[1]
    week3_hours = last_four_week_hours[2]
    week4_hours = last_four_week_hours[3]

    pss_week1 = get_pss_week(PSSWeekModel(Decimal(week1_hours)))

    pss_week2 = get_pss_week(PSSWeekModel(Decimal(week2_hours)))

    pss_week3 = get_pss_week(PSSWeekModel(Decimal(week3_hours)))

    pss_week4 = get_pss_week(PSSWeekModel(Decimal(week4_hours)))

    starting_load_model = LoadStartModel(
        Decimal(pss_week1 / 7),
        Decimal(pss_week2 / 7),
        Decimal(pss_week3 / 7),
        Decimal(pss_week4 / 7),
    )

    starting_load = get_starting_user_load(starting_load_model)
    return starting_load


def get_user_starting_prs(starting_load):
    recovery_index = 0

    # TODO: 4 needs to be replaced
    w_sqs_service = WeightingSqsService(4)
    w_sqs = w_sqs_service.get_weighting_sqs()

    prs_service = PrsService(starting_load, recovery_index, w_sqs)
    prs_today = prs_service.get_prs()

    return prs_today


def get_user_local_date(user):
    timezone_offset = user.timezone_offset
    total_seconds = convert_timezone_offset_to_seconds(timezone_offset)
    user_local_date = (datetime.now() + timedelta(seconds=total_seconds)).date()
    return user_local_date


def save_profile_data(user, request):
    try:
        if request.data.get("profile_data"):
            profile_data, msg = UserProfileService.save_user_profile_data(request, user)
            if not profile_data:
                return None, msg

        if request.data.get("personalise_data"):
            personalise_data, msg = UserProfileService.save_user_personalise_data(
                request, user
            )
            if not personalise_data:
                return None, msg

            if (
                personalise_data.starting_load
                and not ZoneDifficultyLevel.objects.filter(
                    user_auth=user, is_active=True
                ).exists()
            ):
                zone_difficulty_level = ZoneDifficultyLevel(
                    user_auth=user, user_id=user.code
                )
                zone_difficulty_level.set_starting_zone_levels(
                    personalise_data.starting_load
                )
                zone_difficulty_level.save()

        if request.data.get("event_data"):
            user_event, msg = UserEventService.save_user_event_data(request, user)
            if not user_event:
                return None, msg

        package_data = request.data.get("package_data")
        if package_data:
            sub_package_id = package_data.get("sub_package_id")
            UserPackage.objects.create(sub_package_id=sub_package_id, user_id=user.code)

        if request.data.get("schedule_data"):
            schedule_data, msg = UserProfileService.save_user_schedule_data(
                request, user
            )
            if not schedule_data:
                return None, msg

    except Exception as e:
        logger.error(str(e) + "Could not save profile data")
        profile_data_saved = False
        message = str(e)
        return profile_data_saved, message
    else:
        profile_data_saved = True
        message = "Saved profile data successfully"
        return profile_data_saved, message


def update_request_data(request, personalise_data):
    date_of_birth = request.data.get("personalise_data").get("date_of_birth")
    if not date_of_birth and personalise_data.date_of_birth:
        request.data["personalise_data"]["date_of_birth"] = str(
            personalise_data.date_of_birth
        )
    weight = request.data.get("personalise_data").get("weight")
    if not weight and personalise_data.weight:
        request.data["personalise_data"]["weight"] = float(personalise_data.weight)
    current_ftp = request.data.get("personalise_data").get("current_ftp")
    if not current_ftp and personalise_data.current_ftp:
        request.data["personalise_data"]["current_ftp"] = float(
            personalise_data.current_ftp
        )
    max_heart_rate = request.data.get("personalise_data").get("max_heart_rate")
    if not max_heart_rate and personalise_data.max_heart_rate:
        request.data["personalise_data"]["max_heart_rate"] = float(
            personalise_data.max_heart_rate
        )
    current_threshold_heart_rate = request.data.get("personalise_data").get(
        "current_threshold_heart_rate"
    )
    if not current_threshold_heart_rate and personalise_data.current_fthr:
        request.data["personalise_data"]["current_threshold_heart_rate"] = float(
            personalise_data.current_fthr
        )

    return request


def save_user_metadata(**kwargs):
    build_number = kwargs.get("build_number", False)
    device_info = kwargs.get("device_info", False)
    hash_value = kwargs.get("hash_value", False)

    user_meta_data = UserMetaData.objects.filter(
        user_id=kwargs["user_id"], is_active=True
    ).first()
    user_meta_data = (
        create_new_model_instance(user_meta_data) if user_meta_data else UserMetaData()
    )

    user_meta_data.build_number = build_number
    user_meta_data.device_info = device_info
    user_meta_data.hash = hash_value
    user_meta_data.user_id = kwargs["user_id"]

    user_meta_data.save()

    return user_meta_data


class ZoneDifficultyLevelService:
    @classmethod
    def update_zone_difficulty_level(cls, user_auth, planned_session):
        try:
            session = planned_session.session
            if session.difficulty_level is None:
                return
            user_difficulty_level = user_auth.zone_difficulty_levels.filter(
                is_active=True
            ).last()

            zone_focus = session.session_type.get_zone_focus()
            current_level = user_difficulty_level.get_current_level(zone_focus)
            if session.difficulty_level < current_level:
                return

            planned_session_codes = list(
                ActualSession.objects.filter_actual_sessions(
                    user_auth=user_auth,
                    session_code__isnull=False,
                ).values_list("session_code", flat=True)
            )
            planned_session_count = PlannedSession.objects.filter(
                user_auth=user_auth,
                session_code__in=planned_session_codes,
                is_active=True,
                session__session_type__target_zone=session.session_type.target_zone,
                session__difficulty_level=session.difficulty_level,
            ).count()

            if user_difficulty_level.is_zone_upgradable(
                zone_focus, planned_session_count
            ):
                user_difficulty_level.update_zone_level(zone_focus)
                create_new_model_instance(user_difficulty_level)
                user_difficulty_level.save()
        except Exception as e:
            logger.exception(
                "Failed to update zone difficulty level",
                extra=log_extra_fields(
                    user_auth_id=user_auth.id,
                    service_type=ServiceType.INTERNAL.value,
                    exception_message=str(e),
                ),
            )

    @classmethod
    def update_zone_difficulty_level_for_old_user(cls, user_auth):
        try:
            timezone_offset = user_auth.timezone_offset
        except Exception as e:
            logger.info(
                "No timezone info was found",
                extra=log_extra_fields(exception_message=str(e)),
            )
            return

        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )
        actual_day = ActualDay.objects.filter(
            user_auth=user_auth, activity_date=user_local_date, is_active=True
        ).last()
        planned_day = PlannedDay.objects.filter(
            user_auth=user_auth, activity_date=user_local_date, is_active=True
        ).last()
        current_load = 0
        if actual_day:
            current_load = max(actual_day.actual_load, current_load)
        if planned_day:
            current_load = max(planned_day.planned_load, current_load)
        current_load = max(
            user_auth.personalise_data.filter(is_active=True).first().starting_load,
            current_load,
        )

        user_zone_difficulty_level = ZoneDifficultyLevel(
            user_auth=user_auth, user_id=user_auth.code
        )
        user_zone_difficulty_level.set_starting_zone_levels(current_load)
        user_zone_difficulty_level.save()


def save_goal_data(user, request):
    """Saves the necessary event, personalize and schedule data needed to
    create a plan for the user"""
    try:
        if request.data.get("personalise_data"):
            user_personalize_data, msg = UserProfileService.save_personalise_data(
                request, user
            )
            if not user_personalize_data:
                logger.info(
                    msg,
                    extra=log_extra_fields(
                        user_auth_id=user.id, request_url=request.path
                    ),
                )
                return None, msg
            logger.info("Saved personalise data during plan creation")

            from .api.versioned.v2.services import UserProfileServiceV2

            UserProfileServiceV2.save_zone_difficulty_level(user, user_personalize_data)

        if request.data.get("event_data"):
            user_event, msg = UserEventService.save_user_event_data(request, user)
            if not user_event:
                logger.info(
                    msg,
                    extra=log_extra_fields(
                        user_auth_id=user.id, request_url=request.path
                    ),
                )
                return None, msg
            logger.info("Saved event data during plan creation")

        package_data = request.data.get("package_data")
        if package_data:
            sub_package_id = package_data.get("sub_package_id")
            UserPackage.objects.create(sub_package_id=sub_package_id, user_id=user.code)

        if request.data.get("schedule_data"):
            schedule_data, msg = UserProfileService.save_user_schedule_data(
                request, user
            )
            if not schedule_data:
                logger.info(
                    msg,
                    extra=log_extra_fields(
                        user_auth_id=user.id, request_url=request.path
                    ),
                )
                return None, msg
            logger.info("Saved schedule data during plan creation")

    except Exception as e:
        logger.exception(
            "Could not save goal data",
            extra=log_extra_fields(
                user_auth_id=user.id, exception_message=str(e), request_url=request.path
            ),
        )
        goal_data_saved = False
        message = str(e)
        return goal_data_saved, message

    goal_data_saved = True
    message = "Saved goal data successfully"
    logger.info(
        message, extra=log_extra_fields(user_auth_id=user.id, request_url=request.path)
    )
    return goal_data_saved, message


def get_user_starting_load_v2(last_four_week_hours):
    pss_week = get_pss_week(PSSWeekModel(Decimal(last_four_week_hours)))
    pss_daily = Decimal(pss_week / 7)
    return max(MIN_STARTING_LOAD, pss_daily)


class AddNewGoalService:
    def __init__(self, request, user):
        self.no_user_found_msg = "User not found"
        self.event_data_not_found_msg = "User event data not provided"
        self.user_goal_exist_msg = "User already have an active goal"
        self.success_message = (
            "Created new user goal and created training plan successfully"
        )
        self.no_previous_goal_msg = (
            "You are trying to add a new goal but it seems that you dont have"
            " completed any goal yet"
        )
        self.no_personalise_data_msg = (
            "Date since last goal is more than 3 and no personalise data provided"
        )
        self.user = user
        self.request = request
        self.user_event_data = request.data.get("event_data")
        self.user_package_data = request.data.get("package_data")

        self.user_personalise_data = request.data.get("personalise_data")
        self.ctp_activity_code = UserActivityLog.ActivityCode.CREATE_TRAINING_PLAN
        self.add_new_goal_activity_code = UserActivityLog.ActivityCode.ADD_NEW_GOAL

    def add_new_goal(self):
        """Creates a new goal for the user after the previous plan is completed"""

        if not (self.user_event_data or self.user_package_data):
            return PillarResponse(
                self.user,
                self.request,
                make_context(True, self.event_data_not_found_msg, None),
                self.add_new_goal_activity_code,
            )

        user_last_plan = self.user.user_plans.filter(is_active=True).last()
        if not user_last_plan:
            return PillarResponse(
                self.user,
                self.request,
                make_context(True, self.no_previous_goal_msg, None),
                self.add_new_goal_activity_code,
            )

        user_local_date = self.user.user_local_date
        if user_last_plan.end_date >= user_local_date:
            return PillarResponse(
                self.user,
                self.request,
                make_context(True, self.user_goal_exist_msg, None),
                self.add_new_goal_activity_code,
            )

        days_since_last_event = user_local_date - user_last_plan.end_date
        user_previous_personalise_data = self.user.personalise_data.filter(
            is_active=True
        ).last()
        remove_previous_personalize_data = False
        if days_since_last_event.days > 3:
            if not self.user_personalise_data:
                return PillarResponse(
                    self.user,
                    self.request,
                    make_context(True, self.no_personalise_data_msg, None),
                    self.add_new_goal_activity_code,
                )
            if user_previous_personalise_data:
                self.request = update_request_data(
                    self.request, user_previous_personalise_data
                )
            remove_previous_personalize_data = True
        else:
            if self.user_personalise_data:
                self.request.data["personalise_data"] = None

        saved_goal_data, message = save_profile_data(self.user, self.request)
        if not saved_goal_data:
            return PillarResponse(
                self.user,
                self.request,
                make_context(True, message, None),
                self.add_new_goal_activity_code,
            )

        if user_previous_personalise_data and remove_previous_personalize_data:
            user_previous_personalise_data.is_active = False
            user_previous_personalise_data.save()

        update_utp_settings(
            self.user,
            True,
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[2],
            datetime.now() + timedelta(hours=48),
            reason="48 hour rule",
        )

        update_utp_settings(
            self.user,
            self.user.is_third_party_connected(),
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
            datetime.now(),
            reason="",
        )

        if self.user_event_data:
            create_plan(self.user)
        if self.user_package_data:
            package_id = self.user_package_data.get("id")
            user_package_duration = self.user_package_data.get("total_weeks")
            create_package_plan(self.user.code, package_id, user_package_duration)
            create_user_knowledge_hub_entries(self.user, package_id)

        return PillarResponse(
            self.user,
            self.request,
            make_context(False, self.success_message, None),
            self.add_new_goal_activity_code,
        )
