import logging
from datetime import datetime

from core.apps.common.common_functions import get_current_plan
from core.apps.common.const import NO_CURRENT_GOAL
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.daily.utils import get_rides_completed_and_total
from core.apps.event.enums.performance_goal_enum import PerformanceGoalEnum
from core.apps.event.enums.sports_type_enum import SportsTypeEnum
from core.apps.event.models import NamedEvent
from core.apps.plan.enums.goal_type_enum import GoalTypeEnum
from core.apps.plan.utils import is_previous_goal_completed
from core.apps.session.models import PlannedSession, UserAway

from .dictionary import (
    get_event_details_dictionary,
    get_package_details_dictionary,
    get_plan_overview_dictionary,
    get_plan_stats_dictionary,
)

logger = logging.getLogger(__name__)


class PlanServices:
    def __init__(self, user_auth):
        self.user_auth = user_auth
        self.user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            user_auth.timezone_offset, datetime.now()
        )
        self.user_plan = get_current_plan(self.user_auth)
        self.user_event = self.get_user_event()
        self.event_venue = self.get_event_venue()
        self.user_package = self.get_user_package()
        self.has_goal = bool(self.user_event or self.user_package)
        self.goal_type = self.get_goal_type()
        self.named_package = self.user_package.package if self.user_package else None
        self.goal_date = self.get_goal_date()
        self.planned_sessions = self.get_planned_sessions()

        self.goal_name = self.get_user_goal_name()
        self.sports_type = self.get_event_sports_type()
        self.sessions_completed = self.get_sessions_completed()
        self.sessions_remaining = self.get_sessions_remaining()
        self.days_till_goal_complete = self.get_days_till_goal_complete()
        self.goal_progress_percentage = self.get_goal_progress_percentage()

    def get_user_event(self):
        return self.user_plan.user_event if self.user_plan else None

    def get_user_package(self):
        return self.user_plan.user_package if self.user_plan else None

    def get_event_venue(self):
        if self.user_event and self.user_event.named_event_id:
            named_event = NamedEvent.objects.filter(
                pk=self.user_event.named_event_id
            ).last()
            if named_event:
                return (
                    f"{named_event.city}, {named_event.country}"
                    if named_event.city and named_event.country
                    else None
                )

    def get_goal_type(self):
        if self.user_plan:
            return (
                GoalTypeEnum.EVENT.value
                if self.user_event
                else GoalTypeEnum.PACKAGE.value
            )

    def get_goal_date(self):
        if self.user_plan:
            goal_date = (
                self.user_event.start_date
                if self.user_event
                else self.user_plan.end_date
            )
            return DateTimeUtils.get_user_local_date_from_utc(
                self.user_auth.timezone_offset,
                datetime.combine(goal_date, datetime.min.time()),
            )

    def get_user_goal_name(self):
        if not (self.user_event or self.user_package):
            return NO_CURRENT_GOAL
        if self.user_event:
            return self.user_event.name
        return self.named_package.name if self.named_package else None

    def get_event_sports_type(self):
        if not self.user_event:
            return SportsTypeEnum.CYCLING.value
        return self.user_event.sports_type

    def get_planned_sessions(self):
        current_plan = get_current_plan(self.user_auth)
        if current_plan:
            user_away_dates = list(
                UserAway.objects.filter(
                    user_auth=self.user_auth, is_active=True
                ).values_list("away_date", flat=True)
            )
            return PlannedSession.objects.filter(
                user_auth=self.user_auth,
                is_active=True,
                session_date_time__date__gte=current_plan.start_date,
                session_date_time__date__lte=current_plan.end_date,
            ).exclude(session_date_time__in=user_away_dates)
        else:
            return (
                PlannedSession.objects.none()
            )  # Return empty queryset if there is no current plan

    def get_sessions_completed(self):
        sessions_completed, _ = get_rides_completed_and_total(
            self.user_auth, self.planned_sessions
        )
        return sessions_completed

    def get_sessions_remaining(self):
        sessions_remaining = (
            self.planned_sessions.filter(
                session_date_time__date__gte=self.user_local_date
            )
            .exclude(zone_focus=0)
            .count()
        )
        if (
            sessions_remaining
            and self.user_auth.actual_sessions.filter(
                is_active=True,
                session_date_time__date=self.user_local_date,
                session_code__isnull=False,
            ).exists()
        ):
            sessions_remaining -= 1
        return sessions_remaining

    def get_days_till_goal_complete(self):
        if not self.user_event and not self.user_package:
            return 0
        goal_date = (
            self.user_event.start_date if self.user_event else self.user_plan.end_date
        )
        local_goal_date = DateTimeUtils.get_user_local_date_from_utc(
            self.user_auth.timezone_offset,
            datetime.combine(goal_date, datetime.min.time()),
        )
        return (local_goal_date - self.user_local_date).days

    def get_plan_overview(self):
        return get_plan_overview_dictionary(
            goal_name=self.goal_name,
            goal_type=self.goal_type,
            package_type=self.named_package.goal_type if self.named_package else None,
            sports_type=self.sports_type,
            sessions_completed=self.sessions_completed,
            sessions_remaining=self.sessions_remaining,
            has_goal=self.has_goal,
            days_till_goal_complete=self.days_till_goal_complete,
        )

    def get_plan_stats(self):
        return get_plan_stats_dictionary(
            goal_name=self.goal_name,
            sports_type=self.sports_type,
            sessions_completed=self.sessions_completed,
            sessions_remaining=self.sessions_remaining,
            days_till_goal_complete=self.days_till_goal_complete,
            has_goal=self.has_goal,
            previous_goal_completed=is_previous_goal_completed(self.user_auth),
            goal_date=self.goal_date,
            performance_goal=PerformanceGoalEnum.get_text(
                self.user_event.performance_goal
            ).lower()
            if self.user_event
            else None,
            goal_progress_percentage=self.goal_progress_percentage,
        )

    def get_goal_details(self):
        if self.goal_type == GoalTypeEnum.EVENT.value:
            return get_event_details_dictionary(
                goal_name=self.goal_name,
                sports_type=self.sports_type,
                sessions_completed=self.sessions_completed,
                sessions_remaining=self.sessions_remaining,
                days_till_goal_complete=self.days_till_goal_complete,
                goal_date=self.goal_date,
                event_duration_in_days=self.user_event.event_duration_in_days,
                event_venue=self.event_venue,
                goal_progress_percentage=self.goal_progress_percentage,
                event_elevation=f"{round(self.user_event.elevation_gain)} m"
                if self.user_event
                else 0,
                event_distance=f"{round(self.user_event.distance_per_day)} km Ride"
                if self.user_event
                else 0,
            )

        sub_package = self.user_package.sub_package
        return get_package_details_dictionary(
            goal_name=self.goal_name,
            sports_type=self.sports_type,
            sessions_completed=self.sessions_completed,
            sessions_remaining=self.sessions_remaining,
            days_till_goal_complete=self.days_till_goal_complete,
            goal_date=self.goal_date,
            goal_progress_percentage=self.goal_progress_percentage,
            package_duration=self.user_plan.total_days_in_plan,
            sub_package_name=sub_package.name,
            image_url=self.named_package.description_image_url,
            sub_package_icon_url=sub_package.icon_url,
            sub_package_description=sub_package.description,
            knowledge_hub_title=self.named_package.knowledge_hub_title,
            knowledge_hub_description=self.named_package.goal_detail_knowledge_hub_text,
            package_id=self.named_package.id,
        )

    def get_goal_progress_percentage(self):
        user_plan = get_current_plan(self.user_auth)
        if user_plan:
            plan_start_date = user_plan.start_date
            plan_end_date = user_plan.end_date
            plan_days = (plan_end_date - plan_start_date).days
            plan_days_passed = plan_days - self.days_till_goal_complete
            return (plan_days_passed / plan_days) if plan_days else 0
        return 0
