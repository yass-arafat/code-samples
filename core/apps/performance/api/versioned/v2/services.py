import abc
import logging
from datetime import date, datetime, timedelta

from django.db.models import Sum

from core.apps.common.common_functions import get_current_plan, has_pro_feature_access
from core.apps.common.const import (
    ALLOWABLE_PERCENTAGE,
    CURVE_CALCULATION_WINDOWS,
    PRS_BUFFER,
    TWENTY_MINUTE_DATA_ESTIMATE_COEFFICIENT,
)
from core.apps.common.date_time_utils import DateTimeUtils, daterange
from core.apps.common.dictionary.training_zone_dictionary import (
    training_zone_truth_table_dict,
)
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.date_time_format_enum import DateTimeFormatEnum
from core.apps.common.services import RoundServices
from core.apps.common.utils import (
    dakghor_get_time_in_zones,
    get_rounded_freshness,
    initialize_dict,
)
from core.apps.daily.models import ActualDay
from core.apps.daily.utils import get_current_prs
from core.apps.evaluation.daily_evaluation.utils import get_event_target_prs
from core.apps.evaluation.session_evaluation.utils import (
    add_time_in_zones,
    is_time_spent_in_zone,
)
from core.apps.event.enums.performance_goal_enum import PerformanceGoalEnum
from core.apps.session.models import ActualSession, PlannedSession
from core.apps.user_profile.enums.max_zone_difficulty_level_enum import (
    MaxZoneDifficultyLevel,
)
from core.apps.user_profile.utils import get_user_fthr, get_user_ftp
from core.apps.week.models import UserWeek

from .const import PERFORMANCE_TITLE_MESSAGES, PRS_SCORE_REMARKS
from .dictionary import (
    get_freshness_overview_dict,
    get_performance_overview_dict,
    get_performance_stats_dict,
    get_prs_overview_dict,
    get_threshold_overview_dict,
    get_training_load_overview_dict,
)
from .enums import (
    FreshnessPerformanceEnum,
    FreshnessStateEnum,
    ThresholdPerformanceEnum,
    TimeInZonePerformanceEnum,
    TrainingLoadPerformanceEnum,
    ZoneDifficultyLevelPerformanceEnum,
)

logger = logging.getLogger("custom_logger")


class WeekEvaluationServices:
    @staticmethod
    def get_performance_title(
        user_auth, week_start_datetime: datetime, user_local_date, actual_training_time
    ):
        week_day_no = user_local_date.weekday()

        total_training_time = (
            PlannedSession.objects.filter(
                user_auth=user_auth,
                session_date_time__range=(
                    week_start_datetime,
                    week_start_datetime + timedelta(days=7),
                ),
                is_active=True,
            ).aggregate(Sum("planned_duration"))["planned_duration__sum"]
            or 0
        )

        if not total_training_time:
            # This condition has been added so that we don't get a ZeroDivisionError
            training_percentage = ALLOWABLE_PERCENTAGE + 1
        else:
            current_target_training_time = (total_training_time / 7) * (week_day_no + 1)
            training_percentage = (
                actual_training_time - current_target_training_time
            ) / current_target_training_time

        if week_day_no < 2:
            return PERFORMANCE_TITLE_MESSAGES["new_week"]
        elif week_day_no < 6:
            if training_percentage < ALLOWABLE_PERCENTAGE * -1:
                return PERFORMANCE_TITLE_MESSAGES["below_target"]
            elif training_percentage <= ALLOWABLE_PERCENTAGE:
                return PERFORMANCE_TITLE_MESSAGES["on_target"]
            else:
                return PERFORMANCE_TITLE_MESSAGES["above_target"]
        else:
            if training_percentage < ALLOWABLE_PERCENTAGE * -1:
                return PERFORMANCE_TITLE_MESSAGES["target_fail"]
            elif training_percentage <= ALLOWABLE_PERCENTAGE:
                return PERFORMANCE_TITLE_MESSAGES["target_success"]
            else:
                return PERFORMANCE_TITLE_MESSAGES["over_target"]

    @classmethod
    def get_performance_overview(cls, user_auth, user_subscription_status):
        timezone_offset = user_auth.timezone_offset
        current_freshness = None

        week_start_datetime = DateTimeUtils.get_week_start_datetime_for_user(
            user_auth, timezone_offset
        )
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )

        week_end_datetime = DateTimeUtils.get_week_end_datetime_for_user(
            user_auth, timezone_offset
        )
        cycling_type = ActivityTypeEnum.CYCLING.value[1]
        actual_sessions = ActualSession.objects.filter_actual_sessions(
            user_auth,
            session_date_time__range=(week_start_datetime, week_end_datetime),
            activity_type=cycling_type,
        ).aggregate(
            Sum("actual_distance_in_meters"),
            Sum("actual_duration"),
            Sum("elevation_gain"),
        )

        weekly_distance = (
            actual_sessions["actual_distance_in_meters__sum"] or 0
        ) / 1000
        weekly_distance = str(round(weekly_distance, 1)) + " km"

        weekly_elevation = actual_sessions["elevation_gain__sum"] or 0
        weekly_elevation = str(round(weekly_elevation)) + " m"

        weekly_duration = round((actual_sessions["actual_duration__sum"] or 0) * 60)

        actual_day = ActualDay.objects.filter(
            user_auth=user_auth, activity_date=user_local_date, is_active=True
        ).last()

        if has_pro_feature_access(user_subscription_status):
            current_freshness = (actual_day and actual_day.actual_freshness) or 0

        return get_performance_overview_dict(
            title=cls.get_performance_title(
                user_auth, week_start_datetime, user_local_date, weekly_duration
            ),
            weekly_distance=weekly_distance,
            weekly_duration=weekly_duration,
            weekly_elevation=weekly_elevation,
            current_freshness=current_freshness,
        )

    @classmethod
    def get_performance_stats(cls, user_auth):
        timezone_offset = user_auth.timezone_offset
        week_start_datetime = DateTimeUtils.get_week_start_datetime_for_user(
            user_auth, timezone_offset
        )
        week_end_datetime = DateTimeUtils.get_week_end_datetime_for_user(
            user_auth, timezone_offset
        )
        cycling_type = ActivityTypeEnum.CYCLING.value[1]
        actual_sessions = ActualSession.objects.filter_actual_sessions(
            user_auth,
            session_date_time__range=(week_start_datetime, week_end_datetime),
            activity_type=cycling_type,
        ).aggregate(
            Sum("actual_distance_in_meters"),
            Sum("actual_duration"),
            Sum("elevation_gain"),
        )

        weekly_distance = (
            actual_sessions["actual_distance_in_meters__sum"] or 0
        ) / 1000
        weekly_distance = str(round(weekly_distance, 1)) + " km"

        weekly_elevation = actual_sessions["elevation_gain__sum"] or 0
        weekly_elevation = str(round(weekly_elevation)) + " m"

        weekly_duration = round((actual_sessions["actual_duration__sum"] or 0) * 60)

        return get_performance_stats_dict(
            weekly_distance=weekly_distance,
            weekly_duration=weekly_duration,
            weekly_elevation=weekly_elevation,
        )


class PerformancePrsServices:
    @staticmethod
    def get_prs_score_remarks(
        user_auth, user_personalise_obj, current_prs, user_local_date
    ):
        if not current_prs:
            return None
        last_week_actual_day = ActualDay.objects.filter(
            activity_date=user_local_date - timedelta(days=7),
            user_auth=user_auth,
            is_active=True,
        ).last()
        last_week_prs = get_current_prs(
            user_auth, last_week_actual_day, user_personalise_obj
        )

        prs_difference = round(abs(last_week_prs - current_prs))
        if current_prs > last_week_prs + PRS_BUFFER:
            return PRS_SCORE_REMARKS["improving"].format(prs_difference=prs_difference)
        elif current_prs < last_week_prs - PRS_BUFFER:
            return PRS_SCORE_REMARKS["falling"].format(prs_difference=prs_difference)
        return PRS_SCORE_REMARKS["consistent"]

    @classmethod
    def get_prs_overview(cls, user_auth):
        user_personalise_obj = user_auth.personalise_data.filter(is_active=True).last()
        user_plan = get_current_plan(user_auth)
        user_event = user_plan.user_event if user_plan else None

        if not (user_plan and user_event):
            return {}

        starting_prs = round(user_personalise_obj.starting_prs)

        performance_goal = PerformanceGoalEnum.get_text(user_event.performance_goal)
        target_lower_prs, target_upper_prs = get_event_target_prs(
            user_event, performance_goal
        )
        target_prs = RoundServices.round_prs((target_lower_prs + target_upper_prs) / 2)

        timezone_offset = user_auth.timezone_offset
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )
        actual_day = ActualDay.objects.filter(
            user_auth=user_auth, activity_date=user_local_date, is_active=True
        ).last()
        current_prs = get_current_prs(user_auth, actual_day, user_personalise_obj)

        prs_score_remarks = cls.get_prs_score_remarks(
            user_auth, user_personalise_obj, current_prs, user_local_date
        )
        average_session_accuracy_score = (
            round(actual_day.sas_today) if actual_day else 0
        )

        return get_prs_overview_dict(
            current_prs,
            prs_score_remarks,
            starting_prs,
            target_prs,
            average_session_accuracy_score,
        )


class PerformanceFreshnessServices:
    @staticmethod
    def get_current_freshness(user_auth, user_local_date):
        actual_day = ActualDay.objects.filter(
            user_auth=user_auth, activity_date=user_local_date, is_active=True
        ).last()
        if actual_day is None:
            logger.error(
                f"No actual day found for freshness overview api. User ID: {user_auth.id}"
            )
            raise NotImplementedError

        return actual_day.actual_freshness

    @staticmethod
    def get_freshness_title(current_freshness):
        return FreshnessPerformanceEnum.get_title_text(current_freshness)

    @staticmethod
    def get_freshness_remarks(user_auth, user_local_date):
        if user_auth.is_onboarding_week(current_date=user_local_date):
            return FreshnessPerformanceEnum.get_remarks_text(is_onboarding_week=True)

        last_seven_actual_days = ActualDay.objects.filter(
            activity_date__range=(user_local_date - timedelta(days=6), user_local_date),
            user_auth=user_auth,
            is_active=True,
        )
        current_week_freshness_values = [
            actual_day.actual_freshness for actual_day in last_seven_actual_days
        ]
        return FreshnessPerformanceEnum.get_remarks_text(current_week_freshness_values)

    @classmethod
    def get_freshness_overview(cls, user_auth):
        timezone_offset = user_auth.timezone_offset
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )

        current_freshness = cls.get_current_freshness(user_auth, user_local_date)
        freshness_title = cls.get_freshness_title(current_freshness)

        # TODO: Remarks is disabled as it is not consistent with title
        # freshness_remarks = cls.get_freshness_remarks(user_auth, user_local_date)
        freshness_remarks = ""

        return get_freshness_overview_dict(
            current_freshness, freshness_title, freshness_remarks
        )


class PerformanceTrainingLoadServices:
    @staticmethod
    def get_current_load(user_auth, user_local_date):
        actual_day = ActualDay.objects.filter(
            user_auth=user_auth, activity_date=user_local_date, is_active=True
        ).last()
        if actual_day is None:
            logger.error(
                f"No actual day found for training load overview api. User ID: {user_auth.id}"
            )
            raise NotImplementedError
        return actual_day.actual_load

    @staticmethod
    def get_reference_load(user_auth, user_local_date):
        previous_actual_day = ActualDay.objects.filter(
            user_auth=user_auth,
            activity_date=user_local_date - timedelta(days=13),
            is_active=True,
        ).last()
        if previous_actual_day:
            return previous_actual_day.actual_load

    @classmethod
    def get_training_load_overview(cls, user_auth):
        timezone_offset = user_auth.timezone_offset
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )

        current_load = cls.get_current_load(user_auth, user_local_date)
        reference_load = cls.get_reference_load(user_auth, user_local_date)
        load_title, load_remarks = TrainingLoadPerformanceEnum.get_performance_text(
            current_load, reference_load
        )

        return get_training_load_overview_dict(load_title, load_remarks)


class PerformanceThresholdServices:
    @staticmethod
    def is_data_available(curve_data_list, data_key):
        """data_key is either 'power_curve' or 'heart_rate_curve'"""
        for curve_data in curve_data_list:
            if curve_data[data_key] and eval(curve_data[data_key]):
                return True
        return False

    @staticmethod
    def get_max_data_estimate(curve_data_list, data_key):
        max_twenty_minute_data = 0
        max_sixty_minute_data = 0
        for curve_data in curve_data_list:
            data = eval(curve_data[data_key]) if curve_data[data_key] else []
            if data:
                if len(data) > 8:
                    max_twenty_minute_data = max(data[8], max_twenty_minute_data)
                if len(data) > 10:
                    max_sixty_minute_data = max(data[10], max_sixty_minute_data)
        return max(
            max_sixty_minute_data,
            TWENTY_MINUTE_DATA_ESTIMATE_COEFFICIENT * max_twenty_minute_data,
        )

    @classmethod
    def get_threshold_remarks(cls, user_auth):
        power_curve_key = "power_curve"
        heart_rate_curve_key = "heart_rate_curve"
        user_local_date = user_auth.user_local_date

        curve_data_list = user_auth.curve_data.filter(
            is_active=True,
            activity_type=ActivityTypeEnum.CYCLING.value[1],
            activity_datetime__date__range=(
                user_local_date - timedelta(days=30),
                user_local_date,
            ),
        ).values(power_curve_key, heart_rate_curve_key)

        return ThresholdPerformanceEnum.get_threshold_remarks(
            is_power_data_available=cls.is_data_available(
                curve_data_list, power_curve_key
            ),
            is_hr_data_available=cls.is_data_available(
                curve_data_list, heart_rate_curve_key
            ),
            overall_max_power_estimate=cls.get_max_data_estimate(
                curve_data_list, power_curve_key
            ),
            overall_max_hr_estimate=cls.get_max_data_estimate(
                curve_data_list, heart_rate_curve_key
            ),
        )

    @staticmethod
    def get_custom_graph_start_date(user_auth):
        first_curve_data = (
            user_auth.curve_data.filter(
                is_active=True, activity_type=ActivityTypeEnum.CYCLING.value[1]
            )
            .order_by("activity_datetime")
            .values("activity_datetime")
            .first()
        )
        first_curve_data_date = (
            first_curve_data and first_curve_data.get("activity_datetime").date()
        )

        first_plan = (
            user_auth.user_plans.filter(is_active=True)
            .order_by("start_date")
            .values("start_date")
            .first()
        )
        first_plan_date = first_plan and first_plan.get("start_date")

        if first_plan_date and first_curve_data_date:
            return min(first_plan_date, first_curve_data_date)
        return first_plan_date or first_curve_data_date

    @classmethod
    def get_threshold_overview(cls, user_auth):
        return get_threshold_overview_dict(
            current_ftp=get_user_ftp(user_auth, datetime.now()) or None,
            current_fthr=get_user_fthr(user_auth, datetime.now()) or None,
            threshold_remarks=cls.get_threshold_remarks(user_auth),
            custom_graph_start_date=cls.get_custom_graph_start_date(user_auth),
        )


class TimeInZoneOverviewService:
    def __init__(self, user_auth, log_extra_args):
        self.user_auth = user_auth
        self.log_extra_args = log_extra_args
        self.timezone_offset = self.user_auth.timezone_offset
        self.user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            self.timezone_offset, datetime.now()
        )
        self.week_start_datetime = DateTimeUtils.get_week_start_datetime_for_user(
            self.user_auth, self.timezone_offset
        )
        self.week_end_datetime = DateTimeUtils.get_week_end_datetime_for_user(
            self.user_auth, self.timezone_offset
        )
        self.current_week = self.get_current_week()

        self.time_in_zones = self.get_time_in_zones()
        self.time_in_zone_remarks = self.get_time_in_zone_remarks()

    def get_current_week(self):
        logger.info("Fetching current week", extra=self.log_extra_args)
        return UserWeek.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            start_date__lte=self.user_local_date,
            end_date__gte=self.user_local_date,
        ).last()

    def get_total_planned_time_in_zone(self):
        logger.info("Fetching total planned time in zone", extra=self.log_extra_args)
        planned_sessions = PlannedSession.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            session_date_time__range=(self.week_start_datetime, self.week_end_datetime),
        ).values("planned_time_in_power_zone", "planned_time_in_hr_zone")

        total_planned_time_in_zones = initialize_dict(0, 8)
        for planned_session in planned_sessions:
            time_in_power_zone = eval(planned_session["planned_time_in_power_zone"])
            time_in_hr_zone = eval(planned_session["planned_time_in_hr_zone"])
            planned_time_in_zone = (
                time_in_power_zone
                if is_time_spent_in_zone(time_in_power_zone)
                else time_in_hr_zone
            )
            total_planned_time_in_zones = add_time_in_zones(
                total_planned_time_in_zones, planned_time_in_zone
            )
        return total_planned_time_in_zones

    def get_total_actual_time_in_zones(self):
        logger.info("Fetching total actual time in zone", extra=self.log_extra_args)
        athlete_activity_codes = list(
            ActualSession.objects.filter_actual_sessions(
                user_auth=self.user_auth,
                athlete_activity_code__isnull=False,
                session_date_time__range=(
                    self.week_start_datetime,
                    self.week_end_datetime,
                ),
            ).values_list("athlete_activity_code", flat=True)
        )
        actual_time_in_zones = dakghor_get_time_in_zones(athlete_activity_codes)
        total_actual_time_in_zones = initialize_dict(0, 8)
        for time_in_zone in actual_time_in_zones:
            time_in_power_zone = eval(time_in_zone["time_in_power_zone"])
            time_in_hr_zone = eval(time_in_zone["time_in_heart_rate_zone"])
            actual_time_in_zone = (
                time_in_power_zone
                if is_time_spent_in_zone(time_in_power_zone)
                else time_in_hr_zone
            )
            total_actual_time_in_zones = add_time_in_zones(
                total_actual_time_in_zones, actual_time_in_zone
            )
        return total_actual_time_in_zones

    def get_time_in_zones(self):
        total_planned_time_in_zones = (
            self.get_total_planned_time_in_zone() if self.current_week else None
        )
        total_actual_time_in_zones = self.get_total_actual_time_in_zones()

        total_time_spent = 0
        for actual_zone_data in total_actual_time_in_zones:
            total_time_spent += actual_zone_data["value"]

        time_in_zones = []
        logger.info("Building time in zone list", extra=self.log_extra_args)
        for zone_no, actual_zone_data in enumerate(total_actual_time_in_zones):
            actual_time = actual_zone_data["value"]
            planned_time = (
                total_planned_time_in_zones[zone_no]["value"]
                if total_planned_time_in_zones
                else 0
            )
            time_in_zones.append(
                {
                    "zone_no": zone_no,
                    "zone_name": training_zone_truth_table_dict[zone_no]["zone_name"],
                    "time_spent_in_zone": actual_time,
                    "time_planned_in_zone": planned_time,
                    "completion_percentage": round(actual_time * 100 / total_time_spent)
                    if total_time_spent
                    else 0,
                }
            )
        return time_in_zones

    def get_time_in_zone_remarks(self):
        logger.info("Fetching time in zone remarks", extra=self.log_extra_args)
        if not self.current_week:
            return None
        current_week_focus = self.current_week.zone_focus
        return TimeInZonePerformanceEnum.get_time_in_zone_remarks(
            current_date=self.user_local_date,
            current_week_focus=current_week_focus,
            actual_time_in_zone=self.time_in_zones[current_week_focus][
                "time_spent_in_zone"
            ],
            planned_time_in_zone=self.time_in_zones[current_week_focus][
                "time_planned_in_zone"
            ],
        )

    def get_time_in_zone_overview(self):
        return {
            "time_in_zones": sorted(
                self.time_in_zones,
                key=lambda i: (i["time_spent_in_zone"]),
                reverse=True,
            )[:2],
            "time_in_zone_remarks": self.time_in_zone_remarks,
        }


class ZoneDifficultyLevelOverviewService:
    def __init__(self, user_auth, log_extra_args):
        self.user_auth = user_auth
        self.log_extra_args = log_extra_args
        self.zone_difficulty_levels = (
            self.user_auth.zone_difficulty_levels.all().order_by("-id")[:2]
        )

    @staticmethod
    def get_difficulty_level(current_level, zone_no):
        return {
            "zone_no": zone_no,
            "current_level": current_level,
            "max_level": MaxZoneDifficultyLevel.get_max_level(zone_no),
        }

    def get_difficulty_level_remarks(self):
        updated_zone_no = None
        if len(self.zone_difficulty_levels) > 1:
            current_difficulty_level = self.zone_difficulty_levels[0]
            prev_difficulty_level = self.zone_difficulty_levels[1]
            if (
                current_difficulty_level.zone_three_level
                != prev_difficulty_level.zone_three_level
            ):
                updated_zone_no = 3
            if (
                current_difficulty_level.zone_four_level
                != prev_difficulty_level.zone_four_level
            ):
                updated_zone_no = 4
            if (
                current_difficulty_level.zone_five_level
                != prev_difficulty_level.zone_five_level
            ):
                updated_zone_no = 5
            if (
                current_difficulty_level.zone_six_level
                != prev_difficulty_level.zone_six_level
            ):
                updated_zone_no = 6
            if (
                current_difficulty_level.zone_seven_level
                != prev_difficulty_level.zone_seven_level
            ):
                updated_zone_no = 7

        return ZoneDifficultyLevelPerformanceEnum.get_difficulty_level_remarks(
            updated_zone_no
        )

    def get_difficulty_levels(self):
        difficulty_levels = []
        zones = [3, 4, 5, 6, 7]
        if not self.zone_difficulty_levels:
            for zone in zones:
                difficulty_levels.append(
                    self.get_difficulty_level(current_level=0, zone_no=zone)
                )
            return difficulty_levels

        zone_difficulty_level = self.zone_difficulty_levels[0]
        levels = [
            zone_difficulty_level.zone_three_level,
            zone_difficulty_level.zone_four_level,
            zone_difficulty_level.zone_five_level,
            zone_difficulty_level.zone_six_level,
            zone_difficulty_level.zone_seven_level,
        ]
        for level, zone in zip(levels, zones):
            difficulty_levels.append(
                self.get_difficulty_level(current_level=level, zone_no=zone)
            )
        return difficulty_levels

    def get_zone_difficulty_level_overview(self):
        return {
            "difficulty_levels": self.get_difficulty_levels(),
            "difficulty_level_remarks": self.get_difficulty_level_remarks(),
        }


class BaseGraphService:
    def __init__(self, user, year):
        self.user = user

        self.year_start_date = date(year, 1, 1)
        self.year_end_date = date(year, 12, 31)

        self.start_date = self.get_start_date()
        self.end_date = self.get_end_date()

        self.user_active_plans = list(
            user.user_plans.filter(is_active=True)
            .order_by("start_date")
            .values("start_date", "end_date")
        )

    def get_start_date(self):
        return self.year_start_date - timedelta(self.year_start_date.weekday())

    def get_end_date(self):
        return self.year_end_date + timedelta(6 - self.year_end_date.weekday())

    def graph_data(self):
        return {
            "has_previous_data": self.is_previous_year_data_available(),
            "has_next_data": self.is_next_year_data_available(),
            "year": self.year_graph_data(),
        }

    def is_previous_year_data_available(self):
        return bool(
            self.user_active_plans
            and self.user_active_plans[0]["start_date"] < self.year_start_date
        )

    def is_next_year_data_available(self):
        return bool(
            self.user_active_plans
            and self.user_active_plans[-1]["end_date"] > self.year_end_date
        )

    def year_graph_data(self):
        return [
            self.single_data_point(_date)
            for _date in daterange(self.start_date, self.end_date)
        ]

    @abc.abstractmethod
    def single_data_point(self, _date):
        """Returns single data point object for graph"""


class PrsGraphService(BaseGraphService):
    def __init__(self, user, year):
        super().__init__(user, year)

        self.graph_values = {}
        self.get_graph_values()

    def get_graph_values(self):
        self.get_actual_prs_and_sas_today_data()
        self.get_planned_prs_data()
        self.get_session_score_data()

    def get_actual_prs_and_sas_today_data(self):
        query_conditions = {
            "activity_date__range": (self.start_date, self.end_date),
            "is_active": True,
        }
        query_fields = ["activity_date", "prs_accuracy_score", "sas_today"]
        user_actual_days = self.user.actual_days.filter(**query_conditions).values(
            *query_fields
        )

        for actual_day in user_actual_days:
            self.graph_values[actual_day["activity_date"]] = {
                "actual_prs": round(actual_day["prs_accuracy_score"]),
                "sas_today": round(actual_day["sas_today"]),
            }

    def get_planned_prs_data(self):
        user_plans = (
            self.user.user_plans.filter(is_active=True, user_event__isnull=False)
            .select_related("user_event__event_type__details")
            .order_by("start_date")
        )
        for user_plan in user_plans:
            if (
                user_plan.end_date < self.start_date
                or user_plan.start_date > self.end_date
            ):
                continue

            starting_prs = (
                self.user.personalise_data.filter(is_active=True).last().starting_prs
            )
            event_target_prs = self.get_event_target_prs(user_plan.user_event)

            total_days_in_plan = (user_plan.end_date - user_plan.start_date).days
            prs_delta = (
                (event_target_prs - starting_prs) / total_days_in_plan
                if total_days_in_plan
                else 0
            )

            _date_prs = starting_prs
            for _date in daterange(user_plan.start_date, user_plan.end_date):
                if self.start_date <= _date <= self.end_date:
                    if _date in self.graph_values:
                        self.graph_values[_date]["planned_prs"] = round(_date_prs)
                    else:
                        self.graph_values[_date] = {"planned_prs": round(_date_prs)}
                _date_prs += prs_delta

    def get_session_score_data(self):
        actual_sessions = (
            ActualSession.objects.filter_actual_sessions(user_auth=self.user)
            .filter(
                session_date_time__range=(self.start_date, self.end_date),
                session_code__isnull=False,  # Only Evaluated Sessions will be shown
            )
            .select_related("session_score")
        )
        for actual_session in actual_sessions:
            session_score = actual_session.session_score
            if session_score:
                _date = actual_session.session_date_time.date()
                overall_accuracy_score = session_score.get_overall_accuracy_score()
                if _date in self.graph_values:
                    if "session_scores" in self.graph_values[_date]:
                        self.graph_values[_date]["session_scores"].append(
                            overall_accuracy_score
                        )
                    else:
                        self.graph_values[_date].update(
                            {"session_scores": [overall_accuracy_score]}
                        )
                else:
                    self.graph_values[_date] = {
                        "session_scores": [overall_accuracy_score]
                    }

    def year_graph_data(self):
        year_graph_data = []
        for _date in daterange(self.start_date, self.end_date):
            year_graph_data.extend(self.single_data_point(_date))
        return year_graph_data

    def single_data_point(self, _date):
        graph_value = self.graph_values.get(_date)
        session_scores = (graph_value and graph_value.get("session_scores")) or [None]
        return [
            {
                "date": _date,
                "actual_prs": graph_value and graph_value.get("actual_prs"),
                "planned_prs": graph_value and graph_value.get("planned_prs"),
                "session_score_average": graph_value and graph_value.get("sas_today"),
                "individual_score_average": session_score,
            }
            for session_score in session_scores
        ]

    @staticmethod
    def get_event_target_prs(user_event):
        goal_status = PerformanceGoalEnum.get_text(user_event.performance_goal)
        target_lower_prs, target_upper_prs = get_event_target_prs(
            user_event, goal_status
        )
        return round((target_upper_prs + target_lower_prs) / 2)


class FreshnessGraphService(BaseGraphService):
    def __init__(self, user, year):
        super().__init__(user, year)
        self.freshness_data = self.get_freshness_data()

    def get_end_date(self):
        end_date = super().get_end_date()
        timezone_offset = self.user.timezone_offset
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )
        if end_date > user_local_date >= self.year_start_date:
            end_date = user_local_date
        return end_date

    def get_freshness_data(self):
        query_conditions = {
            "activity_date__range": (self.start_date, self.end_date),
            "is_active": True,
        }
        query_fields = ["activity_date", "actual_load", "actual_acute_load"]
        user_actual_days = self.user.actual_days.filter(**query_conditions).values(
            *query_fields
        )

        freshness_values = {}
        for actual_day in user_actual_days:
            freshness_values[actual_day["activity_date"]] = get_rounded_freshness(
                actual_day["actual_load"], actual_day["actual_acute_load"]
            )
        return freshness_values

    def single_data_point(self, _date):
        freshness_value = self.freshness_data.get(_date)
        return {
            "date": _date,
            "freshness_value": freshness_value,
            "freshness_state": FreshnessStateEnum.get_freshness_state(freshness_value),
        }


class ThresholdGraphService:
    def __init__(self, user, start_date: str, end_date: str):
        self.user_auth = user
        self.start_date = datetime.strptime(
            start_date, DateTimeFormatEnum.app_date_format.value
        ).date()
        self.end_date = datetime.strptime(
            end_date, DateTimeFormatEnum.app_date_format.value
        ).date()

        self.power_curve_key = "power_curve"
        self.heart_rate_curve_key = "heart_rate_curve"
        self.activity_datetime_key = "activity_datetime"
        self.curve_data_list = self.user_auth.curve_data.filter(
            is_active=True,
            activity_type=ActivityTypeEnum.CYCLING.value[1],
            activity_datetime__range=(self.start_date, self.end_date),
        ).values(
            self.power_curve_key, self.heart_rate_curve_key, self.activity_datetime_key
        )

        self.is_power_data_available = self.is_data_available(self.power_curve_key)
        self.is_heart_rate_data_available = self.is_data_available(
            self.heart_rate_curve_key
        )
        self.is_weight_available = self.is_user_weight_available()

        self.user_weight_data = self.get_user_weight_data()

    def is_user_weight_available(self):
        return self.user_auth.personalise_data.filter(weight__gt=0).exists()

    def is_previous_data_available(self):
        return self.user_auth.curve_data.filter(
            is_active=True,
            activity_type=ActivityTypeEnum.CYCLING.value[1],
            activity_datetime__date__lt=self.start_date,
        ).exists()

    def is_next_data_available(self):
        return self.user_auth.curve_data.filter(
            is_active=True,
            activity_type=ActivityTypeEnum.CYCLING.value[1],
            activity_datetime__date__gt=self.end_date,
        ).exists()

    def is_data_available(self, data_key):
        """data_key is either 'power_curve' or 'heart_rate_curve'"""
        for curve_data in self.curve_data_list:
            if curve_data[data_key] and eval(curve_data[data_key]):
                return True
        return False

    @staticmethod
    def set_weight_until_end_date(weight_data, weight, current_date, end_date):
        while current_date <= end_date:
            weight_data[current_date] = weight
            current_date += timedelta(days=1)

    def get_user_weight_data(self):
        if not (self.is_weight_available and self.is_power_data_available):
            return {}

        user_personalise_data = list(
            self.user_auth.personalise_data.all().values(
                "created_at", "updated_at", "weight"
            )
        )
        weight_data = {}
        current_date = self.start_date

        for personalise_data in user_personalise_data:
            weight = personalise_data["weight"]
            if not weight:
                continue

            if current_date <= personalise_data["created_at"].date():
                self.set_weight_until_end_date(
                    weight_data,
                    weight,
                    current_date,
                    personalise_data["created_at"].date(),
                )

            if current_date <= personalise_data["updated_at"].date():
                self.set_weight_until_end_date(
                    weight_data,
                    weight,
                    current_date,
                    personalise_data["updated_at"].date(),
                )

            if personalise_data == user_personalise_data[-1]:
                self.set_weight_until_end_date(
                    weight_data, weight, current_date, self.end_date
                )

            if current_date > self.end_date:
                break
        return weight_data

    def get_max_data_info(self, timeframe_index, data_key):
        max_data = None
        max_data_date = None
        for curve_data in self.curve_data_list:
            data_curve = eval(curve_data[data_key]) if curve_data[data_key] else None
            if (
                data_curve
                and len(data_curve) > timeframe_index
                and (max_data is None or max_data < data_curve[timeframe_index])
            ):
                max_data = data_curve[timeframe_index]
                max_data_date = curve_data[self.activity_datetime_key]

        if max_data_date:
            max_data_date = max_data_date.strftime(
                DateTimeFormatEnum.app_date_format.value
            )
        return max_data, max_data_date

    def get_max_power_per_weight_info(self, timeframe_index):
        max_power_per_weight = None
        max_power_per_weight_date = None
        for curve_data in self.curve_data_list:
            data_curve = (
                eval(curve_data[self.power_curve_key])
                if curve_data[self.power_curve_key]
                else []
            )
            weight = self.user_weight_data.get(
                curve_data[self.activity_datetime_key].date()
            )

            if data_curve and len(data_curve) > timeframe_index and weight:
                power_per_weight = data_curve[timeframe_index] / weight
                if (
                    max_power_per_weight is None
                    or max_power_per_weight < power_per_weight
                ):
                    max_power_per_weight = power_per_weight
                    max_power_per_weight_date = curve_data[self.activity_datetime_key]

        if max_power_per_weight_date:
            max_power_per_weight_date = max_power_per_weight_date.strftime(
                DateTimeFormatEnum.app_date_format.value
            )
        return max_power_per_weight, max_power_per_weight_date

    def get_graph_data(self):
        return {
            "has_previous_data": self.is_previous_data_available(),
            "has_next_data": self.is_next_data_available(),
            "is_power_data_available": self.is_power_data_available,
            "is_hr_data_available": self.is_heart_rate_data_available,
            "is_weight_available": self.is_weight_available,
            "graph_data": [
                self.single_data_point(timeframe, timeframe_index)
                for timeframe_index, timeframe in enumerate(CURVE_CALCULATION_WINDOWS)
            ],
        }

    def single_data_point(self, timeframe, timeframe_index):
        graph_data_point = {"timeframe": timeframe}

        if self.is_power_data_available:
            max_power, max_power_date = self.get_max_data_info(
                timeframe_index, self.power_curve_key
            )
            (
                max_power_per_weight,
                max_power_per_weight_date,
            ) = self.get_max_power_per_weight_info(timeframe_index)
            graph_data_point.update(
                {
                    "power": RoundServices.round_power(max_power),
                    "power_date": max_power_date,
                    "power_per_weight": RoundServices.round_power(max_power_per_weight),
                    "power_per_weight_date": max_power_per_weight_date,
                }
            )

        if self.is_heart_rate_data_available:
            max_heart_rate, max_heart_rate_date = self.get_max_data_info(
                timeframe_index, self.heart_rate_curve_key
            )
            graph_data_point.update(
                {
                    "heart_rate": RoundServices.round_heart_rate(max_heart_rate),
                    "heart_rate_date": max_heart_rate_date,
                }
            )

        return graph_data_point


class LoadGraphService:
    def __init__(self, user, start_date, end_date):
        self.user = user
        self.year_start_date = start_date
        self.year_end_date = end_date
        self.first_actual_session_date = self.get_first_actual_session_date()
        self.start_date, self.end_date = self.get_date_range(start_date, end_date)
        (
            self.planned_chronic_load_data,
            self.planned_acute_load_data,
        ) = self.get_planned_load_data(self.user, start_date, end_date)
        (
            self.actual_chronic_load_data,
            self.actual_acute_load_data,
        ) = self.get_actual_load_data(self.user, start_date, end_date)
        self.user_active_plans = list(
            user.user_plans.filter(is_active=True)
            .order_by("start_date")
            .values("start_date", "end_date")
        )

    def get_first_actual_session_date(self):
        first_actual_session = ActualSession.objects.filter(
            user_auth__id=self.user.id, is_active=True
        ).first()
        if first_actual_session:
            first_actual_session_date = first_actual_session.session_date_time.date()
            return first_actual_session_date
        else:
            return None

    @staticmethod
    def get_date_range(start_date, end_date):
        start_date = start_date - timedelta(start_date.weekday())
        end_date = end_date + timedelta(6 - end_date.weekday())
        return start_date, end_date

    @staticmethod
    def get_planned_load_data(user, start_date, end_date):
        query_dict = {"activity_date__range": (start_date, end_date), "is_active": True}
        planned_loads = list(
            user.planned_days.filter(**query_dict).values(
                "activity_date", "planned_load", "planned_acute_load"
            )
        )
        chronic_loads = {}
        acute_loads = {}
        for planned_load in planned_loads:
            chronic_loads[planned_load["activity_date"]] = planned_load["planned_load"]
            acute_loads[planned_load["activity_date"]] = planned_load[
                "planned_acute_load"
            ]
        return chronic_loads, acute_loads

    @staticmethod
    def get_actual_load_data(user, start_date, end_date):
        query_dict = {"activity_date__range": (start_date, end_date), "is_active": True}
        actual_loads = list(
            user.actual_days.filter(**query_dict).values(
                "activity_date", "actual_load", "actual_acute_load"
            )
        )
        chronic_loads = {}
        acute_loads = {}
        for actual_load in actual_loads:
            chronic_loads[actual_load["activity_date"]] = actual_load["actual_load"]
            acute_loads[actual_load["activity_date"]] = actual_load["actual_acute_load"]
        return chronic_loads, acute_loads

    def get_graph_date_range(self):
        graph_start_date = datetime.today().date()
        if self.first_actual_session_date:
            graph_start_date = min(graph_start_date, self.first_actual_session_date)
        if self.user_active_plans:
            first_plan_start_date = self.user_active_plans[0]["start_date"]
            graph_start_date = min(first_plan_start_date, graph_start_date)
        graph_start_date = max(self.start_date.date(), graph_start_date)
        timezone_offset = self.user.timezone_offset
        graph_end_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )
        return graph_start_date, graph_end_date

    def graph_data(self):
        has_previous_data = False
        has_next_data = False
        if self.user_active_plans:
            first_plan_start_date = self.user_active_plans[0]["start_date"]
            last_plan_end_date = self.user_active_plans[-1]["end_date"]
            if first_plan_start_date < self.year_start_date.date():
                has_previous_data = True
            if last_plan_end_date > self.year_end_date.date():
                has_next_data = True
        response_data = {
            "has_previous_data": has_previous_data,
            "has_next_data": has_next_data,
            "year": [],
        }
        _date = self.start_date
        graph_start_date, graph_end_date = self.get_graph_date_range()
        while _date <= self.end_date:
            default_value = 0
            if graph_start_date > _date.date() or _date.date() > graph_end_date:
                default_value = None
            data = {
                "date": _date,
                "chronic_load": RoundServices.round_load(
                    self.planned_chronic_load_data.get(_date.date(), default_value)
                ),
                "acute_load": RoundServices.round_acute_load(
                    self.planned_acute_load_data.get(_date.date(), default_value)
                ),
                "actual_chronic_load": RoundServices.round_load(
                    self.actual_chronic_load_data.get(_date.date(), default_value)
                ),
                "actual_acute_load": RoundServices.round_acute_load(
                    self.actual_acute_load_data.get(_date.date(), default_value)
                ),
            }
            response_data["year"].append(data)
            _date = _date + timedelta(days=1)
        return response_data


class StatsGraphService:
    def __init__(self, user, start_date, end_date):
        self.user = user
        self.year_start_date = start_date
        self.year_end_date = end_date
        self.first_actual_session_date = self.get_first_actual_session_date()
        self.start_date, self.end_date = self.get_date_range(start_date, end_date)
        (
            self.distances_by_date,
            self.actual_durations_by_date,
            self.evaluations_by_date,
        ) = self.calculate_distance_duration_elevation_by_date()
        self.planned_durations_by_date = self.calculate_planned_durations_by_date(
            self.user, start_date, end_date
        )
        self.user_active_plans = list(
            user.user_plans.filter(is_active=True)
            .order_by("start_date")
            .values("start_date", "end_date")
        )

    def get_first_actual_session_date(self):
        first_actual_session = ActualSession.objects.filter(
            user_auth__id=self.user.id, is_active=True
        ).first()
        if first_actual_session:
            first_actual_session_date = first_actual_session.session_date_time.date()
            return first_actual_session_date
        else:
            return None

    @staticmethod
    def get_date_range(start_date, end_date):
        start_date = start_date - timedelta(start_date.weekday())
        end_date = end_date + timedelta(6 - end_date.weekday())
        return start_date, end_date

    @staticmethod
    def calculate_planned_durations_by_date(user, start_date, end_date):
        query_dict = {
            "session_date_time__range": (start_date, end_date),
            "is_active": True,
        }
        durations = list(
            user.planned_sessions.filter(**query_dict).values(
                "planned_duration", "session_date_time"
            )
        )
        durations_by_date = {}
        for duration in durations:
            durations_by_date[duration["session_date_time"].date()] = duration[
                "planned_duration"
            ]
        return durations_by_date

    def calculate_distance_duration_elevation_by_date(self):
        query_dict = {
            "session_date_time__range": (self.start_date, self.end_date),
            "is_active": True,
        }

        actual_session_values = []
        value_fields = [
            "actual_duration",
            "actual_distance_in_meters",
            "session_date_time",
            "activity_type",
            "elevation_gain",
        ]
        actual_sessions = list(
            ActualSession.objects.filter_actual_sessions(user_auth=self.user)
            .filter(**query_dict)
            .values(*value_fields)
        )
        for actual_session in actual_sessions:
            if actual_session["activity_type"] == ActivityTypeEnum.CYCLING.value[1]:
                actual_session_values.append(
                    {
                        "actual_duration": actual_session["actual_duration"],
                        "session_date_time": actual_session["session_date_time"],
                        "actual_distance_in_meters": actual_session[
                            "actual_distance_in_meters"
                        ],
                        "elevation_gain": actual_session["elevation_gain"],
                    }
                )

        distance_by_date = {}
        actual_duration_by_date = {}
        elevations_by_date = {}
        for session_value in actual_session_values:
            session_date = session_value["session_date_time"].date()
            if session_date in distance_by_date:
                distance_by_date[session_date] += session_value[
                    "actual_distance_in_meters"
                ]
                actual_duration_by_date[session_date] += session_value[
                    "actual_duration"
                ]
                elevations_by_date[session_date] += session_value["elevation_gain"]
            else:
                distance_by_date[session_date] = session_value[
                    "actual_distance_in_meters"
                ]
                actual_duration_by_date[session_date] = session_value["actual_duration"]
                elevations_by_date[session_date] = session_value["elevation_gain"]

        return distance_by_date, actual_duration_by_date, elevations_by_date

    def get_graph_date_range(self):
        graph_start_date = datetime.today().date()
        if self.first_actual_session_date:
            graph_start_date = min(graph_start_date, self.first_actual_session_date)
        if self.user_active_plans:
            first_plan_start_date = self.user_active_plans[0]["start_date"]
            graph_start_date = min(first_plan_start_date, graph_start_date)
        graph_start_date = max(self.start_date.date(), graph_start_date)
        timezone_offset = self.user.timezone_offset
        graph_end_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )
        return graph_start_date, graph_end_date

    def graph_data(self):
        has_previous_data = False
        has_next_data = False
        if self.user_active_plans:
            first_plan_start_date = self.user_active_plans[0]["start_date"]
            last_plan_end_date = self.user_active_plans[-1]["end_date"]
            if first_plan_start_date < self.year_start_date.date():
                has_previous_data = True
            if last_plan_end_date > self.year_end_date.date():
                has_next_data = True
        response_data = {
            "has_previous_data": has_previous_data,
            "has_next_data": has_next_data,
            "year": [],
        }
        _date = self.start_date
        graph_start_date, graph_end_date = self.get_graph_date_range()
        while _date <= self.end_date:
            default_value = 0
            if graph_start_date > _date.date() or _date.date() > graph_end_date:
                default_value = None
            data = {
                "date": _date,
                "distance": RoundServices.round_distance(
                    self.distances_by_date.get(_date.date(), default_value)
                ),
                "planned_duration": RoundServices.round_planned_duration_in_minute(
                    self.planned_durations_by_date.get(_date.date(), default_value)
                ),
                "actual_duration": RoundServices.round_actual_duration_in_minute(
                    self.actual_durations_by_date.get(_date.date(), default_value)
                ),
                "elevation": RoundServices.round_elevation(
                    self.evaluations_by_date.get(_date.date(), default_value)
                ),
            }
            response_data["year"].append(data)
            _date = _date + timedelta(days=1)
        return response_data


class TimeInZoneGraphService(BaseGraphService):
    def __init__(self, user, year, log_args):
        super().__init__(user, year)
        self.log_extra_args = log_args
        self.planned_time_in_zones = self.get_planned_time_in_zones()
        self.actual_time_in_zones = self.get_actual_time_in_zones()

    def get_end_date(self):
        end_date = super().get_end_date()
        timezone_offset = self.user.timezone_offset
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )
        if end_date > user_local_date >= self.year_start_date:
            end_date = user_local_date
        return end_date

    def get_planned_time_in_zones(self):
        logger.info("Fetching planned time in zone data", extra=self.log_extra_args)
        planned_sessions = PlannedSession.objects.filter(
            user_auth=self.user,
            is_active=True,
            session_date_time__date__range=(self.start_date, self.end_date),
        ).values(
            "session_date_time", "planned_time_in_power_zone", "planned_time_in_hr_zone"
        )

        planned_time_in_zones = {}
        for planned_session in planned_sessions:
            _date = planned_session["session_date_time"].date().strftime("%Y-%m-%d")
            time_in_power_zone = eval(planned_session["planned_time_in_power_zone"])
            time_in_hr_zone = eval(planned_session["planned_time_in_hr_zone"])
            combined_time_in_zone = (
                time_in_power_zone
                if is_time_spent_in_zone(time_in_power_zone)
                else time_in_hr_zone
            )

            if _date in planned_time_in_zones:
                planned_time_in_zone = planned_time_in_zones[_date]
                time_in_power_zone = add_time_in_zones(
                    planned_time_in_zone["planned_power"], time_in_power_zone
                )
                time_in_hr_zone = add_time_in_zones(
                    planned_time_in_zone["planned_heart_rate"], time_in_hr_zone
                )
                combined_time_in_zone = add_time_in_zones(
                    planned_time_in_zone["planned_combined"], combined_time_in_zone
                )
            else:
                combined_time_in_zone = add_time_in_zones(
                    initialize_dict(0, 8), combined_time_in_zone
                )
            planned_time_in_zones[_date] = {
                "planned_power": time_in_power_zone,
                "planned_heart_rate": time_in_hr_zone,
                "planned_combined": combined_time_in_zone,
            }

        return planned_time_in_zones

    def get_actual_time_in_zones(self):
        logger.info("Fetching actual time in zone data", extra=self.log_extra_args)

        athlete_activity_codes = list(
            ActualSession.objects.filter_actual_sessions(
                user_auth=self.user,
                athlete_activity_code__isnull=False,
                session_date_time__date__range=(self.start_date, self.end_date),
            ).values_list("athlete_activity_code", flat=True)
        )

        logger.info(
            "Fetching time in zone data from Dakghor", extra=self.log_extra_args
        )
        actual_sessions = dakghor_get_time_in_zones(athlete_activity_codes)
        actual_time_in_zones = {}
        for actual_session in actual_sessions:
            _date = actual_session["date"]
            time_in_power_zone = eval(actual_session["time_in_power_zone"])
            time_in_hr_zone = eval(actual_session["time_in_heart_rate_zone"])
            combined_time_in_zone = (
                time_in_power_zone
                if is_time_spent_in_zone(time_in_power_zone)
                else time_in_hr_zone
            )

            if _date in actual_time_in_zones:
                actual_time_in_zone = actual_time_in_zones[_date]
                time_in_power_zone = add_time_in_zones(
                    actual_time_in_zone["actual_power"], time_in_power_zone
                )
                time_in_hr_zone = add_time_in_zones(
                    actual_time_in_zone["actual_heart_rate"], time_in_hr_zone
                )
                combined_time_in_zone = add_time_in_zones(
                    actual_time_in_zone["actual_combined"], combined_time_in_zone
                )
            else:
                combined_time_in_zone = add_time_in_zones(
                    initialize_dict(0, 8), combined_time_in_zone
                )
            actual_time_in_zones[_date] = {
                "actual_power": time_in_power_zone,
                "actual_heart_rate": time_in_hr_zone,
                "actual_combined": combined_time_in_zone,
            }
        return actual_time_in_zones

    def single_data_point(self, _date):
        _date = _date.strftime("%Y-%m-%d")
        datum = {"date": _date}

        if _date in self.planned_time_in_zones:
            datum.update(
                {
                    "planned_power": self.planned_time_in_zones[_date]["planned_power"],
                    "planned_heart_rate": self.planned_time_in_zones[_date][
                        "planned_heart_rate"
                    ],
                    "planned_combined": self.planned_time_in_zones[_date][
                        "planned_combined"
                    ],
                }
            )
        else:
            datum.update(
                {
                    "planned_power": initialize_dict(0, 8),
                    "planned_heart_rate": initialize_dict(0, 7),
                    "planned_combined": initialize_dict(0, 8),
                }
            )

        if _date in self.actual_time_in_zones:
            datum.update(
                {
                    "actual_power": self.actual_time_in_zones[_date]["actual_power"],
                    "actual_heart_rate": self.actual_time_in_zones[_date][
                        "actual_heart_rate"
                    ],
                    "actual_combined": self.actual_time_in_zones[_date][
                        "actual_combined"
                    ],
                }
            )
        else:
            datum.update(
                {
                    "actual_power": initialize_dict(0, 8),
                    "actual_heart_rate": initialize_dict(0, 7),
                    "actual_combined": initialize_dict(0, 8),
                }
            )
        return datum
