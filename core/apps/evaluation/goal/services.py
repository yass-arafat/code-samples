import logging
from datetime import datetime, timedelta

from django.db.models import Count, Q, Sum

from core.apps.common.date_time_utils import DateTimeUtils, daterange
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.services import RoundServices
from core.apps.common.utils import (
    dakghor_get_time_in_zones,
    get_rounded_freshness,
    initialize_dict,
)
from core.apps.daily.models import ActualDay
from core.apps.evaluation.goal.dictionary import goal_evaluation_summary_dict
from core.apps.evaluation.session_evaluation.utils import add_time_in_zones
from core.apps.packages.enums import PackageNameEnum
from core.apps.packages.messages import (
    HILL_CLIMB_PACKAGE_COMPLETION_TEXT,
    PACKAGE_COMPLETION_TEXT,
    RETURN_TO_CYCLING_PACKAGE_COMPLETION_TEXT,
)
from core.apps.performance.api.versioned.v2.enums import FreshnessStateEnum
from core.apps.plan.models import UserPlan
from core.apps.session.models import ActualSession, PlannedSession

logger = logging.getLogger(__name__)


class GoalEvaluationService:
    def __init__(self, user):
        self.user = user

        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            user.timezone_offset, datetime.now()
        )
        self.user_plan = UserPlan.objects.filter(
            user_id=user.code, end_date__lte=user_local_date, is_active=True
        ).last()

        if self.user_plan is None:
            raise ValueError("User have not finished any goal yet.")

        self.start_date = self.user_plan.start_date
        self.end_date = self.user_plan.end_date
        self.cycling_type = ActivityTypeEnum.CYCLING.value[1]

    @classmethod
    def get_goal_evaluation_summary_data(cls, user_id):
        user_plan = UserPlan.objects.filter_with_goal(
            user_id=user_id, is_active=True
        ).last()
        if user_plan.user_package_id is None:
            raise ValueError(f"No selected Package found for user {user_id}")

        user_package = user_plan.user_package
        package_duration = round(user_plan.total_days_in_plan / 7)

        package_completion_text = cls.get_package_completion_text(
            user_package.package.name
        )
        summary_dict = goal_evaluation_summary_dict(
            user_package=user_package.package,
            user_sub_package=user_package.sub_package,
            package_duration=package_duration,
            package_completion_text=package_completion_text,
        )

        logger.info(f"Returning summary dict of user id {user_id} successfully.")
        return summary_dict

    def get_goal_evaluation_stats_data(self):

        logger.info(f"Fetching actual sessions of user id {self.user.code}")

        actual_sessions = ActualSession.objects.filter_actual_sessions(
            self.user,
            session_date_time__date__range=(self.start_date, self.end_date),
            activity_type=self.cycling_type,
        ).aggregate(
            Sum("actual_distance_in_meters"),
            Sum("actual_duration"),
            Sum("elevation_gain"),
            Sum("actual_pss"),
            Count("id"),
        )

        logger.info(f"Successfully fetched actual sessions of user id {self.user.code}")

        distance = (actual_sessions["actual_distance_in_meters__sum"] or 0) / 1000
        distance = str(round(distance, 1)) + " km"

        elevation = actual_sessions["elevation_gain__sum"] or 0
        elevation = str(round(elevation)) + " m"

        duration = round((actual_sessions["actual_duration__sum"] or 0) * 60)
        pss = round((actual_sessions["actual_pss__sum"] or 0) * 60)
        completed_rides = actual_sessions["id__count"]

        logger.info(f"Returning stats dict of user id {self.user.code}")

        return {
            "distance": distance,
            "duration": duration,
            "elevation": elevation,
            "completed_rides": completed_rides,
            "pss": pss,
        }

    def get_goal_evaluation_scores_data(self):

        no_of_planned_sessions = PlannedSession.objects.filter(
            user_id=self.user.code,
            is_active=True,
            session_date_time__date__range=(self.start_date, self.end_date),
        ).count()

        no_of_paired_ride = ActualSession.objects.filter_actual_sessions(
            self.user,
            session_date_time__date__range=(self.start_date, self.end_date),
            activity_type=self.cycling_type,
            session_code__isnull=False,
        ).count()

        actual_days = ActualDay.objects.filter(
            Q(user_id=self.user.code)
            & Q(is_active=True)
            & (Q(activity_date=self.start_date) | Q(activity_date=self.end_date))
        ).order_by("activity_date")
        sas_average = RoundServices.round_sas(actual_days[1].sas_today)

        return {
            "total_sessions": no_of_planned_sessions,
            "completed_sessions": no_of_paired_ride,
            "session_accuracy_score_average": sas_average,
            "goal_start_load": RoundServices.round_load(actual_days[0].actual_load),
            "goal_end_load": RoundServices.round_load(actual_days[1].actual_load),
            "goal_start_prs": RoundServices.round_prs(
                actual_days[0].prs_accuracy_score
            ),
            "goal_end_prs": RoundServices.round_prs(actual_days[1].prs_accuracy_score),
        }

    @classmethod
    def get_package_completion_text(cls, user_package_name):
        if user_package_name == PackageNameEnum.get_value("RETURN_TO_CYCLING"):
            package_completion_text = RETURN_TO_CYCLING_PACKAGE_COMPLETION_TEXT
        elif user_package_name == PackageNameEnum.get_value("HILL_CLIMB"):
            package_completion_text = HILL_CLIMB_PACKAGE_COMPLETION_TEXT
        else:
            package_completion_text = PACKAGE_COMPLETION_TEXT

        return package_completion_text


class GoalEvaluationBaseGraphService:
    def __init__(self, user):
        self.user = user
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            user.timezone_offset, datetime.now()
        )
        self.user_plan = UserPlan.objects.filter(
            user_id=user.code, end_date__lte=user_local_date, is_active=True
        ).last()

        if self.user_plan is None:
            raise ValueError("User have not finished any goal yet.")

        self.start_date = self.user_plan.start_date
        self.end_date = self.user_plan.end_date

    def get_graph_data(self):
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "data_points": self._get_data_points(),
        }

    def _get_data_points(self):
        return [
            self._single_data_point(_date)
            for _date in daterange(self.start_date, self.end_date)
        ]

    def _single_data_point(self, _date):
        """Returns single data point object for graph"""
        pass


class GoalEvaluationTrainingLoadGraph(GoalEvaluationBaseGraphService):
    def __init__(self, user):
        super().__init__(user)
        self.actual_loads = {}
        self.actual_acute_loads = {}
        self._get_actual_loads_and_actual_acute_loads()

    def _get_actual_loads_and_actual_acute_loads(self):
        query_conditions = {
            "activity_date__range": (self.start_date, self.end_date),
            "is_active": True,
        }
        actual_loads = list(
            self.user.actual_days.filter(**query_conditions).values(
                "activity_date", "actual_load", "actual_acute_load"
            )
        )
        for actual_load in actual_loads:
            self.actual_loads[actual_load["activity_date"]] = actual_load["actual_load"]
            self.actual_acute_loads[actual_load["activity_date"]] = actual_load[
                "actual_acute_load"
            ]

    def _single_data_point(self, _date):
        default_value = 0
        actual_load = RoundServices.round_load(
            self.actual_loads.get(_date, default_value)
        )
        actual_acute_load = RoundServices.round_acute_load(
            self.actual_acute_loads.get(_date, default_value)
        )
        return {
            "date": _date,
            "actual_load": actual_load,
            "actual_acute_load": actual_acute_load,
        }


class GoalEvaluationFreshnessGraph(GoalEvaluationBaseGraphService):
    def __init__(self, user):
        super().__init__(user)
        self.freshness_data = self.get_freshness_data()

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

    def _single_data_point(self, _date):
        freshness_value = self.freshness_data.get(_date)
        return {
            "date": _date,
            "freshness_value": freshness_value,
            "freshness_state": FreshnessStateEnum.get_freshness_state(freshness_value),
        }


class GoalEvaluationTimeInZoneGraphService(GoalEvaluationBaseGraphService):
    def __init__(self, user, log_args):
        super().__init__(user)
        self.user_personalise_data = self.user.personalise_data.filter(
            is_active=True
        ).last()

        self.log_extra_args = log_args
        self.planned_time_in_zones = self._get_planned_time_in_zones()
        self.actual_time_in_zones = self._get_actual_time_in_zones()

    def _get_planned_time_in_zones(self):
        logger.info("Fetching planned time in zone data", extra=self.log_extra_args)
        planned_sessions = PlannedSession.objects.filter(
            user_auth=self.user,
            is_active=True,
            session_date_time__date__range=(self.start_date, self.end_date),
        ).values(
            "session_date_time", "planned_time_in_power_zone", "planned_time_in_hr_zone"
        )

        planned_time_in_power_zones = initialize_dict(0, 8)
        planned_time_in_hr_zones = initialize_dict(0, 7)
        for planned_session in planned_sessions:
            time_in_power_zone = eval(planned_session["planned_time_in_power_zone"])
            time_in_hr_zone = eval(planned_session["planned_time_in_hr_zone"])

            planned_time_in_power_zones = add_time_in_zones(
                planned_time_in_power_zones, time_in_power_zone
            )
            planned_time_in_hr_zones = add_time_in_zones(
                planned_time_in_hr_zones, time_in_hr_zone
            )

        return {
            "planned_power": planned_time_in_power_zones,
            "planned_heart_rate": planned_time_in_hr_zones,
        }

    def _get_actual_time_in_zones(self):
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

        actual_time_in_power_zones = initialize_dict(0, 8)
        actual_time_in_hr_zones = initialize_dict(0, 7)
        for actual_session in actual_sessions:
            time_in_power_zone = eval(actual_session["time_in_power_zone"])
            time_in_hr_zone = eval(actual_session["time_in_heart_rate_zone"])

            actual_time_in_power_zones = add_time_in_zones(
                actual_time_in_power_zones, time_in_power_zone
            )
            actual_time_in_hr_zones = add_time_in_zones(
                actual_time_in_hr_zones, time_in_hr_zone
            )

        return {
            "actual_power": actual_time_in_power_zones,
            "actual_heart_rate": actual_time_in_hr_zones,
        }

    def get_graph_data(self):
        return {
            "is_ftp_available": bool(self.user_personalise_data.current_ftp),
            "is_fthr_available": bool(self.user_personalise_data.current_fthr),
            "data_points": self._get_data_points(),
        }

    def _get_data_points(self):
        return self._single_data_point(_date=None)

    def _single_data_point(self, _date):
        return {**self.planned_time_in_zones, **self.actual_time_in_zones}


class GoalEvaluationTimeVsDistanceGraph(GoalEvaluationBaseGraphService):
    def __init__(self, user):
        super().__init__(user)
        self.distances = {}
        self.actual_durations = {}
        self._calculate_distances_and_actual_durations()

        self.weeks = self._create_weeks()

    def _calculate_distances_and_actual_durations(self):
        query_fields = [
            "actual_duration",
            "actual_distance_in_meters",
            "session_date_time",
        ]
        actual_sessions = list(
            ActualSession.objects.filter_actual_sessions(
                user_auth=self.user,
                session_date_time__range=(self.start_date, self.end_date),
                activity_type=ActivityTypeEnum.CYCLING.value[1],
            ).values(*query_fields)
        )

        for session_value in actual_sessions:
            session_date = session_value["session_date_time"].date()
            if session_date in self.distances:
                self.distances[session_date] += session_value[
                    "actual_distance_in_meters"
                ]
                self.actual_durations[session_date] += session_value["actual_duration"]
            else:
                self.distances[session_date] = session_value[
                    "actual_distance_in_meters"
                ]
                self.actual_durations[session_date] = session_value["actual_duration"]

    def _create_weeks(self):
        week_start_date = self.start_date
        weeks = []
        while week_start_date <= self.end_date:
            week_end_date = min(week_start_date + timedelta(days=6), self.end_date)
            weeks.append({"start_date": week_start_date, "end_date": week_end_date})
            week_start_date = week_end_date + timedelta(days=1)
        return weeks

    def get_graph_data(self):
        return {
            "data_points": self._get_data_points(),
        }

    def _get_data_points(self):
        data_points = []
        for week in self.weeks:
            data_point = {
                "date": week["start_date"],
                "actual_duration": 0,
                "distance": 0,
            }
            for _date in daterange(week["start_date"], week["end_date"]):
                data_point["actual_duration"] += self.actual_durations.get(_date, 0)
                data_point["distance"] += self.distances.get(_date, 0)

            data_point["actual_duration"] = round(
                data_point["actual_duration"] * 60
            )  # convert from min to sec
            data_point["distance"] = RoundServices.round_distance(
                data_point["distance"]
            )
            data_points.append(data_point)
        return data_points
