import calendar
import json
import logging
from datetime import date, datetime, time, timedelta

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response

from core.apps.daily.models import ActualDay

from ..plan.enums.goal_type_enum import GoalTypeEnum
from ..user_profile.models import UserActivityLog
from .const import MIN_STARTING_LOAD
from .date_time_utils import DateTimeUtils
from .dictionary.training_zone_dictionary import training_zone_truth_table_dict
from .enums.service_enum import ServiceType
from .enums.subscription_status import SubscriptionStatusEnum
from .utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)

calendar.setfirstweekday(calendar.MONDAY)
logger = logging.getLogger(__name__)


class CommonClass:
    """
    common class
    """

    @classmethod
    def get_zone_focus_from_power(cls, cur_ftp, power):
        for idx in training_zone_truth_table_dict:
            upper_power_bound = (
                training_zone_truth_table_dict[idx]["power_ftp_upper_bound"] / 100
            ) * cur_ftp
            if power <= upper_power_bound:
                return training_zone_truth_table_dict[idx]["zone_focus"]

    @classmethod
    def get_zone_focus_from_ftp(cls, ftp):
        for idx in training_zone_truth_table_dict:
            upper_ftp_bound = training_zone_truth_table_dict[idx][
                "power_ftp_upper_bound"
            ]
            if ftp <= upper_ftp_bound:
                return training_zone_truth_table_dict[idx]["zone_focus"]

    @classmethod
    def get_zone_focus_from_fthr(cls, fthr):
        if fthr < training_zone_truth_table_dict[0]["heart_rate_fthr_lower_bound"]:
            return training_zone_truth_table_dict[0]["zone_focus"]

        for idx in training_zone_truth_table_dict:
            # This condition will be true when we reach zone focus 6. For HR, zone 6 is the limit
            if (
                training_zone_truth_table_dict[idx]["heart_rate_fthr_upper_bound"]
                == 106
            ):
                return training_zone_truth_table_dict[idx]["zone_focus"]

            upper_fthr_bound = training_zone_truth_table_dict[idx][
                "heart_rate_fthr_upper_bound"
            ]
            if fthr <= upper_fthr_bound:
                return training_zone_truth_table_dict[idx]["zone_focus"]

    @classmethod
    def get_zone_focus_from_hr(cls, cur_fthr, hr):
        lowest_hr_bound = (
            training_zone_truth_table_dict[0]["heart_rate_fthr_lower_bound"] / 100
        ) * cur_fthr
        if hr < lowest_hr_bound:
            # HR is lower than 25% of fthr
            return training_zone_truth_table_dict[0]["zone_focus"]

        for idx in training_zone_truth_table_dict:
            # This condition will be true when we reach zone focus 6. For HR, zone 6 is the limit
            if (
                training_zone_truth_table_dict[idx]["heart_rate_fthr_upper_bound"]
                == 106
            ):
                return training_zone_truth_table_dict[idx]["zone_focus"]

            upper_hr_bound = (
                training_zone_truth_table_dict[idx]["heart_rate_fthr_upper_bound"] / 100
            ) * cur_fthr
            if hr <= upper_hr_bound:
                return training_zone_truth_table_dict[idx]["zone_focus"]

    @classmethod
    def get_zone_focus_from_max_hr(cls, max_hr):
        if max_hr < training_zone_truth_table_dict[0]["max_heart_rate_lower_bound"]:
            return training_zone_truth_table_dict[0]["zone_focus"]

        for idx in training_zone_truth_table_dict:
            upper_max_hr_bound = training_zone_truth_table_dict[idx][
                "max_heart_rate_upper_bound"
            ]
            if max_hr <= upper_max_hr_bound:
                return training_zone_truth_table_dict[idx]["zone_focus"]

    @classmethod
    def get_zone_focus_from_hr_by_max_hr(cls, max_hr, hr):
        lowest_hr_bound = (
            training_zone_truth_table_dict[0]["max_heart_rate_lower_bound"] / 100
        ) * max_hr
        if hr < lowest_hr_bound:
            return training_zone_truth_table_dict[0]["zone_focus"]

        for idx in training_zone_truth_table_dict:
            upper_max_hr_bound = (
                training_zone_truth_table_dict[idx]["max_heart_rate_upper_bound"] / 100
            ) * max_hr
            if hr <= upper_max_hr_bound:
                return training_zone_truth_table_dict[idx]["zone_focus"]

    @classmethod
    def get_time_zone_list_dict(cls, timezones):
        ls = []
        for tz in timezones:
            ls_obj = {
                "timezone_id": tz.id,
                "timezone_name": tz.name,
                "timezone_offset": tz.offset,
                "timezone_type": tz.type,
            }
            ls.append(ls_obj)
        return ls


def format_timezone(tz: str):
    if tz[0] == "-" or tz[0] == "+":
        return tz
    return "+" + tz


def get_yesterday(day):
    """Returns the previous day object for creating training plan"""
    if day.date <= date.today():
        return None
    user = day.user_auth
    yesterday_date = day.date - timedelta(days=1)
    return user.planned_days.get(date=yesterday_date, is_active=True)


def get_load_start_for_user(user):
    user_data = user.personalise_data.filter(is_active=True).first()
    return user_data.starting_load


def get_acute_load_start_for_user(user):
    user_data = user.personalise_data.filter(is_active=True).first()
    return user_data.starting_acute_load


def get_actual_day_yesterday(user, activity_date):
    """Returns the previous actual day object for evaluation"""
    date_yesterday = activity_date - timedelta(days=1)
    day_yesterday = user.actual_days.filter(
        activity_date=date_yesterday, is_active=True
    ).last()

    user_personalise_data = user.personalise_data.filter(is_active=True).first()
    if user_personalise_data:
        starting_load = user_personalise_data.starting_load
        starting_acute_load = user_personalise_data.starting_acute_load
    else:
        # In case user do not have personalise data
        starting_load = MIN_STARTING_LOAD
        starting_acute_load = MIN_STARTING_LOAD

    is_onboarding_day = False
    day_yesterday = user.actual_days.filter(
        activity_date=date_yesterday, is_active=True
    ).last()

    user_personalise_data = user.personalise_data.filter(is_active=True).first()

    if day_yesterday:
        date_before_onboarding = user.created_at - timedelta(days=1)

        if day_yesterday.activity_date == date_before_onboarding:
            day_yesterday.actual_load = starting_load
            day_yesterday.actual_acute_load = starting_acute_load
            day_yesterday.sqs_today = dict(day_yesterday.SQS_CHOICES)["STARTING_SQS"]
            day_yesterday.sas_today = dict(day_yesterday.SQS_CHOICES)["STARTING_SAS"]
            is_onboarding_day = True
    else:
        # Activity date is onboarding day
        day_yesterday = ActualDay()  # This won't be saved in DB
        day_yesterday.actual_load = starting_load
        day_yesterday.actual_acute_load = starting_acute_load
        day_yesterday.sqs_today = dict(day_yesterday.SQS_CHOICES)["STARTING_SQS"]
        day_yesterday.sas_today = dict(day_yesterday.SQS_CHOICES)["STARTING_SAS"]
        is_onboarding_day = True

    return day_yesterday, is_onboarding_day


def clear_cache():
    cache.clear()


def clear_user_cache(user=None, user_id=None):
    prefix = user_id + ":*"
    user_keys = cache.keys(prefix)
    cache.delete_many(user_keys)
    logger.info(
        "Cleared user cache",
        extra=log_extra_fields(
            user_auth_id=user_id, service_type=ServiceType.INTERNAL.value
        ),
    )


def clear_user_cache_with_prefix(prefix, user_id):
    user_keys = cache.keys("*" + prefix + "*")
    cache.delete_many(user_keys)
    logger.info(
        "Cleared user cache",
        extra=log_extra_fields(
            user_id=user_id, service_type=ServiceType.INTERNAL.value
        ),
    )


def clear_cache_with_key(key):
    cache.delete(key)


def get_timezone_offset_from_seconds(seconds):
    """
    Converts seconds difference into timezone offset.
    Safe to assume it returns from "+13:00" to "-10:30"
    :param seconds
    :return: timezone offset in str format
    """
    time_diff = round((seconds / 60) / 30) * 30 / 60
    if time_diff > 13:
        time_diff -= 24
    elif time_diff <= -11:
        time_diff += 24

    hour_str = str(int(time_diff))
    if time_diff >= 0:
        hour_str = "+" + hour_str
    elif time_diff == -0.5:
        # Among negative offsets, only for "-0:30", "-" has to be added manually
        hour_str = "-" + hour_str

    if time_diff.is_integer():
        minute_str = ":00"
    else:
        minute_str = ":30"

    timezone_offset = hour_str + minute_str
    return timezone_offset


def get_timezone_offset_from_datetime_diff(time_diff):
    """
    Converts difference between two datetime objects into timezone offset.
    Safe to assume it returns from "+13:00" to "-10:30"
    :param time_diff
    :return: timezone offset in str format
    """
    return get_timezone_offset_from_seconds(time_diff.total_seconds())


def get_auto_update_start_date(today=None):
    if today is None:
        today = date.today()
    if today.weekday() == 0:
        return today
    return today + timedelta(days=(7 - today.weekday()))


def get_auto_update_start_datetime():
    return datetime.combine(get_auto_update_start_date(), time(0, 5, 0))


def get_current_plan(user):
    today = DateTimeUtils.get_user_local_date_from_utc(
        user.timezone_offset, datetime.now()
    )
    plan = user.user_plans.filter(
        is_active=True, start_date__lte=today, end_date__gte=today
    ).last()
    return plan


def get_date_from_datetime(input_date_time):
    if type(input_date_time) == datetime:
        return input_date_time.date()
    return input_date_time


def remove_exponent(num):
    return num.to_integral() if num == num.to_integral() else num.normalize()


def get_user_current_goal_type(user):
    user_plan = get_current_plan(user)
    if user_plan:
        return GoalTypeEnum.goal_type_of_plan(user_plan)


def pro_feature(func):
    def wrapper_func(class_reference, request, *args, **kwargs):
        if not has_pro_feature_access(request.session["user_subscription_status"]):
            user = get_user_from_session_destroy_session_variable(request)
            logger.error(
                "An unauthorized user tried to access pro feature",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )

            return Response(
                make_context(
                    True,
                    "This feature can not be accessed in basic subscription, "
                    "please upgrade to Pro",
                    None,
                ),
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        logger.info(
            "User has pro feature access",
            extra=log_extra_fields(
                user_auth_id=request.session["user_auth"].id,
                service_type=ServiceType.API.value,
                request_url=request.path,
            ),
        )

        return func(class_reference, request, *args, **kwargs)

    return wrapper_func


def has_pro_feature_access(user_subscription_status):
    subscription_status = user_subscription_status.lower()
    if subscription_status in (
        SubscriptionStatusEnum.PRO.value.lower(),
        SubscriptionStatusEnum.TRIAL.value.lower(),
    ):
        return True
    return False


def cache_data(func):
    def wrapper_func(class_reference, request, *args, **kwargs):
        try:
            force_refresh = request.GET.get("force_refresh")
            athlete_code = request.session["user_id"]
            cache_key = athlete_code + "&" + request.path + "&" + request.method
            if request.method == "POST":
                cache_key = cache_key + "&" + json.dumps(request.data)
            if (lambda x, y: x != "true" and y in cache)(force_refresh, cache_key):
                cached_data = cache.get(cache_key)
                logger.info("Returning data from cache")
                return Response(
                    make_context(False, "Returned data successfully", cached_data),
                    status=status.HTTP_200_OK,
                )
            kwargs["cache_key"] = cache_key

            return func(class_reference, request, *args, **kwargs)
        except Exception as e:
            logger.exception("Cache issue", log_extra_fields(exception_message=str(e)))

    return wrapper_func


def pillar_response(activity_code=None):
    def decorator(func):
        success_msg = "Returned data Successfully"
        error_message = "Could not return data successfully"

        def wrapper_func(class_reference, request, *args, **kwargs):
            user_id = request.session.get("user_id")
            result = None
            status_code = status.HTTP_200_OK
            try:
                result = func(class_reference, request, *args, **kwargs)
                response = make_context(message=success_msg, data=result)
            except PermissionDenied as e:
                logger.exception(
                    error_message,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        service_type=ServiceType.API.value,
                    ),
                )

                response = make_context(error=True, message=error_message)
                status_code = (status.HTTP_403_FORBIDDEN,)

            except Exception as e:
                logger.exception(
                    error_message,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_id=request.session["user_id"],
                        service_type=ServiceType.API.value,
                    ),
                )

                response = make_context(error=True, message=error_message)
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            if activity_code:
                try:
                    UserActivityLog.objects.create(
                        user_id=user_id,
                        request=request.data,
                        response=response,
                        activity_code=activity_code,
                        data=result,
                    )
                    logger.info(
                        f"User activity log created for user {user_id} and actiivty {activity_code}"
                    )
                except Exception as e:
                    logger.exception(
                        "Could not log user activity",
                        extra=log_extra_fields(
                            exception_message=str(e),
                            request_url=request.path,
                            user_id=request.session["user_id"],
                            service_type=ServiceType.API.value,
                        ),
                    )

            return Response(response, status=status_code)

        return wrapper_func

    return decorator
