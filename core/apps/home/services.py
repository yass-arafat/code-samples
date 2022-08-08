import logging
import random
from datetime import datetime, timedelta

from django.db.models import Count, Sum

from core.apps.common.const import LOWEST_PLAN_LENGTH
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.tp_common_utils import is_third_party_connected
from core.apps.daily.serializers import DayActualSessionSerializer
from core.apps.event.api.base.serializers import EventNameSerializer
from core.apps.event.models import NamedEvent
from core.apps.plan.enums.goal_type_enum import GoalTypeEnum
from core.apps.session.models import ActualSession

logger = logging.getLogger(__name__)


class RecentRideService:
    @staticmethod
    def get_recent_ride_data(user):
        """Returns the required data for the last/recent activity tile of user"""
        last_ride_actual_session = ActualSession.objects.filter_actual_sessions(
            user_auth=user, activity_type=ActivityTypeEnum.CYCLING.value[1]
        ).last()
        recent_ride_data = DayActualSessionSerializer(
            last_ride_actual_session,
            context={"user": user},
        ).data
        logger.info(f"Recent ride data for user ID: {user.id} returned successfully")
        return {"activities": [recent_ride_data]}


class HomePageService:
    @staticmethod
    def get_base_home_page_data(user, pro_feature_access):
        """Returns the required data to design base home page widget"""
        user_code = user.code
        user_local_date = user.user_local_date
        user_plan = user.user_plans.filter_with_goal(
            end_date__gte=user_local_date, is_active=True
        ).last()

        if user_plan and pro_feature_access:
            # Not in Ride & Record Mode
            old_home = True
            # if user plan is package then show basic stats
            weekly_stats = bool(user_plan.user_package_id)
            try_a_goal = (
                last_activity
            ) = encourage_to_connect = encourage_to_record = False
        else:
            # user is in Ride & Record Mode
            old_home, try_a_goal = False, True
            if is_third_party_connected(user_code):
                encourage_to_connect = False

                actual_session_exists = ActualSession.objects.filter(
                    user_auth=user,
                    is_active=True,
                    activity_type=ActivityTypeEnum.CYCLING.value[1],
                ).exists()
                encourage_to_record = not actual_session_exists
                weekly_stats = last_activity = actual_session_exists
            else:
                encourage_to_connect = True
                weekly_stats = encourage_to_record = last_activity = False

        user_last_plan = user.user_plans.filter_with_goal(is_active=True).last()
        if user_last_plan:
            days_due_of_event = user_last_plan.days_due_of_event(user_local_date)
            # TODO: This is temporary fix. Update the logic for is_goal_completed
            is_goal_completed = bool(-2 <= days_due_of_event < 0)
            goal_type = GoalTypeEnum.goal_type_of_plan(user_last_plan)
        else:
            days_due_of_event = 0
            is_goal_completed = False
            goal_type = None

        base_home_page_data = {
            # old_home should be False if is_goal_completed is True
            "old_home": old_home,
            "try_a_goal": try_a_goal,
            "weekly_stats": weekly_stats,
            "encourage_to_connect": encourage_to_connect,
            "encourage_to_record": encourage_to_record,
            "last_activity": last_activity,
            "days_due_of_event": days_due_of_event,
            # is_goal_completed should be False if old_home is True
            "is_goal_completed": is_goal_completed,
            "goal_type": goal_type,
        }
        logger.info(
            f"Base home page data for user ID: {user.id} returning successfully"
        )
        return base_home_page_data

    @staticmethod
    def get_home_page_event_list(user):
        minimum_event_date = datetime.today() + timedelta(days=LOWEST_PLAN_LENGTH)
        named_event_list = NamedEvent.objects.filter(
            is_active=True, end_date__gte=minimum_event_date
        ).order_by("name")

        serializer = EventNameSerializer(
            named_event_list, context={"offset": user.timezone_offset}, many=True
        )
        all_named_event_list_data = serializer.data
        named_event_list_data = random.sample(all_named_event_list_data, k=4)

        return {"goals": named_event_list_data}

    @staticmethod
    def get_weekly_stats(user):
        timezone_offset = user.timezone_offset
        week_start_datetime = DateTimeUtils.get_week_start_datetime_for_user(
            user, timezone_offset
        )
        week_end_datetime = DateTimeUtils.get_week_end_datetime_for_user(
            user, timezone_offset
        )
        cycling_type = ActivityTypeEnum.CYCLING.value[1]
        actual_sessions = ActualSession.objects.filter_actual_sessions(
            user,
            session_date_time__range=(week_start_datetime, week_end_datetime),
            activity_type=cycling_type,
        ).aggregate(
            Sum("actual_distance_in_meters"),
            Sum("actual_duration"),
            Count("id"),
        )

        weekly_completed_rides = actual_sessions["id__count"]
        weekly_distance = (
            actual_sessions["actual_distance_in_meters__sum"] or 0
        ) / 1000
        weekly_distance = str(round(weekly_distance, 1)) + " km"
        weekly_duration = round((actual_sessions["actual_duration__sum"] or 0) * 60)

        weekly_stats = {
            "weekly_distance": weekly_distance,
            "weekly_duration": weekly_duration,
            "weekly_completed_rides": weekly_completed_rides,
        }
        logger.info(f"Weekly stats for: {user.id} returned successfully")
        return weekly_stats
