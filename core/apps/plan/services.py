import asyncio
import datetime
import logging
import math
from calendar import monthrange

from django.db.models import Q

from core.apps.block.models import UserBlock
from core.apps.common.date_time_utils import DateTimeUtils, convert_str_date_to_date_obj
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    create_new_model_instance,
    log_extra_fields,
    most_common_item_in_list,
    update_is_active_value,
)
from core.apps.daily.models import PlannedDay
from core.apps.session.models import PlannedSession
from core.apps.week.models import UserWeek, WeekAnalysis

from ..packages.models import UserKnowledgeHub
from .month_plan_async import async_main
from .month_plan_utils import merge_data
from .utils import day_details_for_month, get_day_details_for_month

logger = logging.getLogger(__name__)


class PlanService:
    @classmethod
    def get_my_month_plan_details(cls, user, year, month):
        _, no_of_days = monthrange(int(year), int(month))
        start_date_str = year + "-" + month + "-1"
        end_date_str = year + "-" + month + "-" + str(no_of_days)

        calendar_start_date = convert_str_date_to_date_obj(start_date_str)
        calendar_end_date = convert_str_date_to_date_obj(end_date_str)

        day_details_list = get_day_details_for_month(
            user, calendar_start_date, calendar_end_date
        )
        return day_details_list

    @classmethod
    def month_plan_details(cls, user, year: int, month: int):
        _, last_day_of_month = monthrange(year, month)
        calendar_start_date = datetime.date(year=year, month=month, day=1)
        calendar_end_date = datetime.date(year=year, month=month, day=last_day_of_month)

        day_details_list = day_details_for_month(
            user, calendar_start_date, calendar_end_date
        )
        return day_details_list

    @classmethod
    def calendar_details_async(
        cls, user, year, month, pro_feature_access, padding=False
    ):
        _, last_day_of_month = monthrange(year, month)
        calendar_start_date = datetime.date(year=year, month=month, day=1)
        calendar_end_date = datetime.date(year=year, month=month, day=last_day_of_month)
        if padding:
            calendar_start_date = DateTimeUtils.get_week_start_date(calendar_start_date)
            calendar_end_date = DateTimeUtils.get_week_end_date(calendar_end_date)

        results = asyncio.run(
            async_main(user, calendar_start_date, calendar_end_date, pro_feature_access)
        )
        results = merge_data(results)

        week_analysis_codes = cls.get_week_analysis_codes(
            user, calendar_start_date, calendar_end_date
        )
        response_data = cls.add_week_analysis_codes(user, results, week_analysis_codes)

        return response_data

    @classmethod
    def add_week_analysis_codes(cls, user, results, week_analysis_codes):
        """
        Adds week analysis codes in the response.
        If a week analysis report starts on one of the days in the report,
        that day then will store the code field of the WeekAnalysis model.
        Otherwise it will contain None.
        """
        logger.info(
            "Adding week analysis into calendar response",
            extra=log_extra_fields(
                user_auth_id=user.id,
                user_id=user.code,
                service_type=ServiceType.API.value,
            ),
        )
        for day_object in results:
            code = week_analysis_codes.get(day_object["date"])
            day_object["week_analysis_id"] = code
            if code:
                week_analysis_codes.pop(day_object["date"])

        for key, value in week_analysis_codes.items():
            results.append({"date": key, "week_analysis_id": value})
        return results

    @staticmethod
    def get_week_analysis_codes(user, start_date, end_date):
        """
        Fetches all WeekAnalysis objects whose start dates are within the range of
        the month and returns them in a dictionary format where the keys are the start
        dates of the objects and the values are the uuid codes.
        """
        logger.info(
            "Fetching week analysis for calendar view",
            extra=log_extra_fields(
                user_auth_id=user.id,
                user_id=user.code,
                service_type=ServiceType.API.value,
            ),
        )
        week_analysis_objects = WeekAnalysis.objects.filter_active(
            user_id=user.code, report_date__range=(start_date, end_date)
        ).values("report_date", "code")

        week_analysis_codes = {}
        for week_analysis in week_analysis_objects:
            week_analysis_codes[week_analysis["report_date"]] = week_analysis["code"]
        return week_analysis_codes


class DeleteTrainingPlan:
    def __init__(self, user_auth, new_plan_end_date):
        self.new_plan_end_date = new_plan_end_date
        self.user_auth = user_auth
        self.user_plan = self.user_auth.user_plans.filter(is_active=True).last()
        self.user_goal = self.user_plan.user_goal

        self.log_extra_fields = log_extra_fields(
            user_auth_id=self.user_auth.id, service_type=ServiceType.API.value
        )

    def delete_user_plan(self):
        logger.info("Deleting user plan", extra=self.log_extra_fields)
        if self.user_plan.start_date > self.new_plan_end_date:
            # This will happen if user deletes the goal the same day of creating
            # the plan and didn't pair any ride. We can deactivate every plan
            # related entries in this case.
            logger.info("Deleting user plan completely", extra=self.log_extra_fields)
            self._delete_complete_plan()
            return

        update_is_active_value([self.user_goal], False)
        self._update_user_goal()
        self._update_user_plan()
        self._update_current_block()
        self._deactivate_rows_under_plan(start_date=self._get_valid_date())

    def _delete_complete_plan(self):
        user_blocks = UserBlock.objects.filter(
            plan_code=self.user_plan.plan_code, is_active=True
        )

        block_codes = [user_block.block_code for user_block in user_blocks]
        user_weeks = UserWeek.objects.filter(block_code__in=block_codes, is_active=True)

        week_codes = [user_week.week_code for user_week in user_weeks]
        planned_days = PlannedDay.objects.filter(
            week_code__in=week_codes, is_active=True
        )

        day_codes = [planned_day.day_code for planned_day in planned_days]
        planned_sessions = PlannedSession.objects.filter(
            day_code__in=day_codes, is_active=True
        )

        user_knowledge_hub_entries = UserKnowledgeHub.objects.filter(
            user_id=self.user_auth.code,
            activation_date__gte=self.user_plan.start_date,
            is_active=True,
        )

        update_is_active_value(user_blocks, False)
        update_is_active_value(user_weeks, False)
        update_is_active_value(planned_days, False)
        update_is_active_value(planned_sessions, False)
        update_is_active_value([self.user_goal], False)
        update_is_active_value([self.user_plan], False)
        update_is_active_value(user_knowledge_hub_entries, False)

    def _update_user_plan(self):
        create_new_model_instance(self.user_plan)
        self.user_plan.end_date = self.new_plan_end_date
        self.user_plan.save()

    def _update_user_goal(self):
        if self.user_plan.user_event_id:
            create_new_model_instance(self.user_goal)
            self.user_goal.start_date = self.new_plan_end_date
            self.user_goal.end_date = self.new_plan_end_date
            self.user_goal.save()
            self.user_plan.user_event = self.user_goal

    def _update_current_block(self):
        current_block = self.user_auth.user_blocks.filter(
            is_active=True,
            start_date__lte=self.new_plan_end_date,
            end_date__gte=self.new_plan_end_date,
        ).last()
        incomplete_block_start_date = current_block.start_date
        number_of_days_in_new_block = (
            self.new_plan_end_date - incomplete_block_start_date
        )

        current_block.no_of_weeks = max(
            math.ceil(number_of_days_in_new_block.days / 7), 1
        )
        current_block.end_date = self.new_plan_end_date

        current_block = create_new_model_instance(current_block)
        current_block.save()

    def _deactivate_rows_under_plan(self, start_date):
        logger.info("Deleting table rows under plan", extra=self.log_extra_fields)

        user_blocks = UserBlock.objects.filter(
            user_auth=self.user_auth, start_date__gte=start_date, is_active=True
        )
        user_weeks = UserWeek.objects.filter(
            user_auth=self.user_auth, start_date__gte=start_date, is_active=True
        )
        planned_days = PlannedDay.objects.filter(
            user_auth=self.user_auth, activity_date__gte=start_date, is_active=True
        )
        planned_sessions = PlannedSession.objects.filter(
            user_auth=self.user_auth, session_date_time__gte=start_date, is_active=True
        )
        user_knowledge_hub_entries = UserKnowledgeHub.objects.filter(
            user_id=self.user_auth.code, activation_date__gte=start_date, is_active=True
        )

        update_is_active_value(user_blocks, False)
        update_is_active_value(user_weeks, False)
        update_is_active_value(planned_days, False)
        update_is_active_value(planned_sessions, False)
        update_is_active_value(user_knowledge_hub_entries, False)

    def _get_valid_date(self):
        return self.new_plan_end_date + datetime.timedelta(days=1)


class WeekInfoService:
    @staticmethod
    def get_week_info(user, year, month):
        _, last_day_of_month = monthrange(year, month)
        # Calendar weeks start from Monday and ends in Sunday
        start_date = DateTimeUtils.get_week_start_date(
            datetime.date(year=year, month=month, day=1)
        )
        end_date = DateTimeUtils.get_week_end_date(
            datetime.date(year=year, month=month, day=last_day_of_month)
        )
        user_weeks = user.user_weeks.filter(
            Q(start_date__range=(start_date, end_date))
            | Q(end_date__range=(start_date, end_date)),
            is_active=True,
        )
        planned_days = user.planned_days.filter(
            activity_date__range=(start_date, end_date), is_active=True
        )
        week_focus_list = []

        while start_date < end_date:
            user_week = user_weeks.filter(start_date=start_date).last()
            # If user week starts from Monday, we can get the zone focus directly
            if user_week:
                week_focus = user_week.zone_focus
            # If user week doesn't start from Monday, then calendar week's zone focus
            # will be the most frequent zone focus among the planned days of that week
            else:
                week_end_date = start_date + datetime.timedelta(days=6)
                week_planned_days = planned_days.filter(
                    activity_date__range=(start_date, week_end_date)
                ).values_list("zone_focus", flat=True)
                week_focus = most_common_item_in_list(week_planned_days)

            week_focus_list.append(week_focus)
            start_date += datetime.timedelta(days=7)

        return {"week_focus": week_focus_list}
