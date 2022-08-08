import datetime
import logging
from decimal import Decimal

from core.apps.common.common_functions import get_date_from_datetime
from core.apps.daily.models import ActualDay
from core.apps.event.enums.performance_goal_enum import PerformanceGoalEnum

from .api.base.serializers import (
    ActualDayPrsAccuracySerializer,
    UserLastSevenDaysRISerializer,
    UserLastSevenDaysSASSerializer,
    UserLastSevenDaysSQSSerializer,
)
from .dictionary import (
    get_daily_prs_dictionary,
    get_load_graph_dictionary,
    get_seven_days_ri_dict,
    get_seven_days_sqs_dict,
)
from .utils import (
    get_daily_prs,
    get_daily_target_prs,
    get_days_planned_load,
    get_event_target_prs,
)

logger = logging.getLogger(__name__)


class UserDailyEvaluation:
    @classmethod
    def get_daily_prs(cls, user, utc_today_date):
        user_plan = user.user_plans.filter(is_active=True).last()
        onboarding_date = user_plan.start_date

        try:
            user_event = user_plan.user_event
        except Exception as e:
            logger.exception(str(e) + "User Event Not found")
            return None

        goal_status = PerformanceGoalEnum.get_text(user_event.performance_goal)

        # get target event lower and upper prs
        target_lower_prs, target_upper_prs = get_event_target_prs(
            user_event, goal_status
        )

        # get daily prs from onboarding day to today's date
        daily_prs_range_end_date = utc_today_date
        if user_event.end_date < get_date_from_datetime(utc_today_date):
            daily_prs_range_end_date = user_event.end_date

        daily_actual_prs = get_daily_prs(
            onboarding_date, daily_prs_range_end_date, user
        )

        starting_prs = user.personalise_data.filter(is_active=True).first().starting_prs

        if not daily_actual_prs:
            first_day_prs = {
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "value": starting_prs,
            }
            daily_actual_prs = []
            daily_actual_prs.append(first_day_prs)

        daily_target_prs = get_daily_target_prs(
            onboarding_date,
            user_event.end_date,
            starting_prs,
            target_lower_prs,
            target_upper_prs,
        )

        return get_daily_prs_dictionary(
            daily_actual_prs=daily_actual_prs,
            daily_target_prs=daily_target_prs,
            goal_status=goal_status,
            event_date=user_event.end_date,
            event_name=user_event.name,
            event_distance=user_event.distance_per_day,
        )

    @classmethod
    def get_prs_graph(cls, user, utc_today_date):
        user_plan = user.user_plans.filter(is_active=True).last()
        onboarding_date = user_plan.start_date

        try:
            user_event = user_plan.user_event
        except Exception as e:
            logger.exception(str(e) + "User Event Not found")
            return None

        goal_status = PerformanceGoalEnum.get_text(user_event.performance_goal)

        # get target event lower and upper prs
        target_lower_prs, target_upper_prs = get_event_target_prs(
            user_event, goal_status
        )

        # get daily prs from onboarding day to today's date
        daily_prs_range_end_date = utc_today_date
        if user_event.end_date < get_date_from_datetime(utc_today_date):
            daily_prs_range_end_date = user_event.end_date

        actual_day_list = ActualDay.objects.filter(
            activity_date__range=(onboarding_date, daily_prs_range_end_date),
            user_auth=user,
            is_active=True,
        ).order_by("activity_date")
        serialized = ActualDayPrsAccuracySerializer(
            actual_day_list, many=True, context={"offset": user.timezone_offset}
        )

        daily_actual_prs = serialized.data

        starting_prs = user.personalise_data.filter(is_active=True).first().starting_prs

        if not daily_actual_prs:
            first_day_prs = {
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "value": starting_prs,
            }
            daily_actual_prs = []
            daily_actual_prs.append(first_day_prs)

        daily_target_prs = get_daily_target_prs(
            onboarding_date,
            user_event.end_date,
            starting_prs,
            target_lower_prs,
            target_upper_prs,
        )

        return get_daily_prs_dictionary(
            daily_actual_prs=daily_actual_prs,
            daily_target_prs=daily_target_prs,
            goal_status=goal_status,
            event_date=user_event.end_date,
            event_name=user_event.name,
            event_distance=user_event.distance_per_day,
        )

    @classmethod
    def get_last_seven_days_recovery_index(cls, user, utc_date_today):
        user_plan = user.user_plans.filter(is_active=True).last()
        user_event = user_plan.user_event
        end_date = utc_date_today

        if get_date_from_datetime(user_event.event_date) < get_date_from_datetime(
            end_date
        ):
            end_date = user_event.event_date

        start_date = end_date - datetime.timedelta(days=7)
        if get_date_from_datetime(start_date) < get_date_from_datetime(
            user_plan.start_date
        ):
            start_date = user_plan.start_date

        seven_days_user_day_data = ActualDay.objects.filter(
            user_auth=user, activity_date__range=(start_date, end_date), is_active=True
        ).order_by("activity_date")
        if not seven_days_user_day_data:
            first_day_ri = {
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "value": 0,
            }
            ri_list = []
            ri_list.append(first_day_ri)
            return get_seven_days_ri_dict(ri_list)
        else:
            serialized = UserLastSevenDaysRISerializer(
                seven_days_user_day_data,
                many=True,
                context={"offset": user.timezone_offset},
            )
        return get_seven_days_ri_dict(serialized.data)

    @classmethod
    def get_last_seven_days_sqs(cls, user, utc_date_today):
        user_plan = user.user_plans.filter(is_active=True).last()
        user_event = user_plan.user_event

        end_date = utc_date_today

        if get_date_from_datetime(user_event.event_date) < get_date_from_datetime(
            end_date
        ):
            end_date = user_event.event_date

        start_date = end_date - datetime.timedelta(days=7)
        if get_date_from_datetime(start_date) < get_date_from_datetime(
            user_plan.start_date
        ):
            start_date = user_plan.start_date

        seven_days_user_day_data = ActualDay.objects.filter(
            user_auth=user, activity_date__range=(start_date, end_date), is_active=True
        ).order_by("activity_date")
        if not seven_days_user_day_data:
            first_day_sqs = {
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "value": Decimal(dict(ActualDay.SQS_CHOICES)["STARTING_SQS"]),
            }
            sqs_list = []
            sqs_list.append(first_day_sqs)
            return get_seven_days_sqs_dict(sqs_list)
        else:
            serialized = UserLastSevenDaysSQSSerializer(
                seven_days_user_day_data,
                many=True,
                context={"offset": user.timezone_offset},
            )
            return get_seven_days_sqs_dict(serialized.data)

    @classmethod
    def get_last_seven_days_sas(cls, user, utc_date_today):
        user_plan = user.user_plans.filter(is_active=True).last()
        user_event = user_plan.user_event

        end_date = utc_date_today

        if get_date_from_datetime(user_event.event_date) < get_date_from_datetime(
            end_date
        ):
            end_date = user_event.event_date

        start_date = end_date - datetime.timedelta(days=7)
        if get_date_from_datetime(start_date) < get_date_from_datetime(
            user_plan.start_date
        ):
            start_date = user_plan.start_date

        seven_days_user_day_data = ActualDay.objects.filter(
            user_auth=user, is_active=True, activity_date__range=(start_date, end_date)
        ).order_by("activity_date")

        if not seven_days_user_day_data:
            return {
                "sas_graph": [
                    {
                        "date": datetime.date.today().strftime("%Y-%m-%d"),
                        "value": Decimal(dict(ActualDay.SQS_CHOICES)["STARTING_SAS"]),
                    }
                ]
            }
        else:
            serializer = UserLastSevenDaysSASSerializer(
                seven_days_user_day_data,
                many=True,
                context={"offset": user.timezone_offset},
            )
            return {"sas_graph": serializer.data}

    @classmethod
    def get_load_graph_data(cls, user):
        user_plan = user.user_plans.filter(is_active=True).last()
        onboarding_date = user_plan.start_date
        utc_today_date = datetime.date.today()
        user_event = user_plan.user_event
        event_date_time = user_event.event_date

        target_load_list = get_days_planned_load(user, onboarding_date, event_date_time)
        if get_date_from_datetime(user_event.event_date) < get_date_from_datetime(
            utc_today_date
        ):
            utc_today_date = user_event.event_date
        load_today = (
            ActualDay.objects.values_list("actual_load", flat=True)
            .filter(user_auth=user, activity_date=utc_today_date, is_active=True)
            .last()
        )
        if not load_today:
            load_today = (
                user.personalise_data.filter(is_active=True).last().starting_load
            )
        load_today = round(load_today, 1)
        today_date = get_date_from_datetime(utc_today_date)

        return get_load_graph_dictionary(target_load_list, load_today, today_date)
