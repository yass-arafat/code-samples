import logging

from django.db import connections

from core.apps.common.dictionary.training_zone_dictionary import (
    training_zone_truth_table_dict,
)
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.services import RoundServices
from core.apps.common.utils import log_extra_fields
from core.apps.evaluation.daily_evaluation.utils import get_event_target_prs
from core.apps.event.enums.performance_goal_enum import PerformanceGoalEnum
from core.apps.plan.models import UserPlan

from .dictionary import get_today_dictionary
from .models import ActualDay, PlannedDay
from .utils import (
    get_current_prs,
    get_today_session_details,
    get_total_distance_covered_from_onboarding_day,
    today_session_details,
)

logger = logging.getLogger(__name__)


class UserDailyServices:

    # Depreciated from R7
    @classmethod
    def get_today_details(cls, user_auth, utc_today_date, user_local_date):
        user_last_plan = user_auth.user_plans.filter(is_active=True).last()
        user_event = user_last_plan.user_event
        days_due_of_event = (user_event.start_date - utc_today_date).days
        if days_due_of_event < 0:
            logger.error(
                "Event date has been expired",
                extra=log_extra_fields(user_auth_id=user_auth.id),
            )
            return {
                "today_date": user_local_date,
                "days_due_of_event": days_due_of_event,
            }
        try:
            day_data = ActualDay.objects.filter(
                user_auth=user_auth, activity_date=utc_today_date, is_active=True
            ).last()
            if not day_data:
                day_data = PlannedDay.objects.filter(
                    user_auth=user_auth, activity_date=utc_today_date, is_active=True
                ).last()

            zone_focus_name = training_zone_truth_table_dict[day_data.zone_focus][
                "zone_name"
            ]
            zone_focus = training_zone_truth_table_dict[day_data.zone_focus][
                "zone_focus"
            ]

            user_personalise_obj = user_auth.personalise_data.filter(
                is_active=True
            ).first()
            starting_prs = round(user_personalise_obj.starting_prs)
            # When user will not be under any plan then there will be NO planned day or actual day
            # Setting prs 0 in this case, if products share different view we will change it
            current_prs = (
                0
                if day_data is None
                else get_current_prs(user_auth, day_data, user_personalise_obj)
            )

            (
                rides_completed,
                rides_total,
                upcoming_rides,
                past_rides,
            ) = get_today_session_details(user_auth, utc_today_date)

            total_plan_distance = get_total_distance_covered_from_onboarding_day(
                user_auth
            )
            logger.info("Got total_plan_distance")

            logger.info("Got days_due_of_event")

            target_prs, _ = get_event_target_prs(
                user_event, PerformanceGoalEnum.get_text(user_event.performance_goal)
            )

            if current_prs > target_prs:
                current_prs = target_prs

            if current_prs < 0:
                current_prs = 0

        except Exception as e:
            logger.exception(
                "Today details not found",
                extra=log_extra_fields(
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    user_id=user_auth.code,
                    user_auth_id=user_auth.id,
                ),
            )
            return {"details": "not found"}

        return get_today_dictionary(
            user_local_date,
            zone_focus_name,
            zone_focus,
            starting_prs,
            current_prs,
            target_prs,
            rides_completed,
            rides_total,
            total_plan_distance,
            days_due_of_event,
            upcoming_rides,
            past_rides,
        )

    @classmethod
    def today_details(cls, user_auth):
        user_local_date = user_auth.user_local_date
        user_plan = UserPlan.objects.filter_with_goal(
            user_auth=user_auth, end_date__gte=user_local_date, is_active=True
        ).last()
        if user_plan:
            days_due_of_event = user_plan.days_due_of_event(user_local_date)
        else:
            days_due_of_event = 0

        if days_due_of_event < 0:
            return {
                "today_date": user_local_date,
                "days_due_of_event": days_due_of_event,
            }

        try:
            day_data = ActualDay.objects.filter(
                user_auth=user_auth, activity_date=user_local_date, is_active=True
            ).last()
            if not day_data:
                day_data = PlannedDay.objects.filter(
                    user_auth=user_auth, activity_date=user_local_date, is_active=True
                ).last()

            zone_focus_name = training_zone_truth_table_dict[day_data.zone_focus][
                "zone_name"
            ]
            zone_focus = training_zone_truth_table_dict[day_data.zone_focus][
                "zone_focus"
            ]

            user_personalise_obj = user_auth.personalise_data.filter(
                is_active=True
            ).first()
            starting_prs = round(user_personalise_obj.starting_prs)
            current_prs = get_current_prs(user_auth, day_data, user_personalise_obj)

            (
                rides_completed,
                rides_total,
                upcoming_rides,
                past_rides,
            ) = today_session_details(user_auth, user_local_date)

            total_plan_distance = get_total_distance_covered_from_onboarding_day(
                user_auth
            )
            logger.info("Got total_plan_distance")

            if user_plan and user_plan.user_event_id:
                user_event = user_plan.user_event
                target_lower_prs, target_upper_prs = get_event_target_prs(
                    user_event,
                    PerformanceGoalEnum.get_text(user_event.performance_goal),
                )
                target_prs = (target_lower_prs + target_upper_prs) / 2
                target_prs = RoundServices.round_prs(target_prs)
            else:
                target_prs = 0

            if current_prs > target_prs:
                current_prs = target_prs

            if current_prs < 0:
                current_prs = 0

        except Exception as e:
            logger.exception(
                "Today details not found",
                extra=log_extra_fields(
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    user_id=user_auth.code,
                    user_auth_id=user_auth.id,
                ),
            )
            return {"details": "not found"}

        return get_today_dictionary(
            user_local_date,
            zone_focus_name,
            zone_focus,
            starting_prs,
            current_prs,
            target_prs,
            rides_completed,
            rides_total,
            total_plan_distance,
            days_due_of_event,
            upcoming_rides,
            past_rides,
        )


class DayMigrationService:
    @classmethod
    def migrate_day_data(cls, user):
        """Migrate data from UserDay table to PlannedDay and ActualDay table for selected user"""

        error = False
        try:
            logger.info("starts migrating user day to planned day")
            cls.migrate_user_day_data_to_planned_day(user)

            logger.info("starts migrating user day id to actual day")
            cls.migrate_user_day_data_to_actual_day(user)

            logger.info("User day migration finished successfully")

        except Exception as e:
            logger.info(str(e))
            error = True

        return error

    @classmethod
    def migrate_user_day_data_to_planned_day(cls, user):
        """Migrate UserDay table record to PlannedDay table for selected user"""
        raw_query = (
            f"INSERT INTO planned_day(user_auth_id, activity_date, max_load, training_pss_by_load, "
            f"training_pss_by_hours, training_pss_by_max_ride, training_pss_by_freshness, "
            f"training_pss_final_value, planned_load, planned_acute_load, planned_pss, load_post_commute, "
            f"acute_load_post_commute, commute_pss_day, zone_focus, is_active, created_at, "
            f"updated_at, day_code, week_code) "
            f"SELECT user_auth_id, activity_date, max_load, training_pss_by_load, training_pss_by_hours, "
            f"training_pss_by_max_ride, training_pss_by_freshness, training_pss_final_value, planned_load, "
            f"planned_acute_load, planned_pss, load_post_commute, acute_load_post_commute, "
            f"commute_pss_day, zone_focus, is_active, created_at, updated_at, day_code, week_code "
            f"FROM user_day WHERE user_auth_id = {user.id}"
        )

        cursor = connections["default"].cursor()
        cursor.execute(raw_query)

    @classmethod
    def migrate_user_day_data_to_actual_day(cls, user):
        """Migrate UserDay table record to ActualDay table for selected user"""

        raw_query = (
            f"INSERT INTO actual_day(user_auth_id, activity_date, actual_load, actual_acute_load, "
            f"actual_pss, zone_focus, recovery_index, is_active, prs_score, sqs_today, created_at, "
            f"updated_at, day_code, week_code) "
            f"SELECT user_auth_id, activity_date, actual_load, actual_acute_load, actual_pss, zone_focus, "
            f"recovery_index, is_active, prs_score, sqs_today ,created_at, updated_at, day_code, week_code "
            f"FROM user_day WHERE activity_date <= CURRENT_DATE and user_auth_id = {user.id}"
        )

        cursor = connections["default"].cursor()
        cursor.execute(raw_query)
