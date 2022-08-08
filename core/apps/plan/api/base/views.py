import logging

from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import has_pro_feature_access
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)

from ...services import PlanService, WeekInfoService

logger = logging.getLogger(__name__)


class AsyncMonthPlanView(APIView):
    def get(self, request, year, month):
        user = get_user_from_session_destroy_session_variable(request)
        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        log_extra_data = log_extra_fields(
            user_auth_id=user.id,
            request_url=request.path,
            service_type=ServiceType.API.value,
        )
        cache_key = f"{user.email}:get_my_month_plan_view_async{year}-{month}"
        logger.info("Calendar API is called", extra=log_extra_data)

        if cache_key in cache and not force_refresh:
            month_plan_dict_list = cache.get(cache_key)
            logger.info("Returning calendar data from cache", extra=log_extra_data)

            return Response(
                make_context(
                    False, "Month Plan returned successfully.", month_plan_dict_list
                )
            )

        try:
            padding = request.GET.get("padding")
            pro_feature_access = has_pro_feature_access(
                request.session["user_subscription_status"]
            )
            month_plan_dict_list = PlanService.calendar_details_async(
                user, year, month, pro_feature_access, padding
            )
        except Exception as e:
            logger.exception(
                f"Failed to return calendar data for user ID: {str(user.code)}, "
                f"month: {month}, year: {year}.",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    request_url=request.path,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                ),
            )
            return Response(make_context(True, "Failed to fetch calendar data", None))

        cache.set(cache_key, month_plan_dict_list, timeout=settings.CACHE_TIME_OUT)
        logger.info("Returning calendar data (not from cache)", extra=log_extra_data)

        return Response(
            make_context(
                False, "Month Plan returned successfully.", month_plan_dict_list
            )
        )


class WeekInfoView(APIView):
    success_msg = "Week info returned successfully"

    def get(self, request, year, month):
        user = get_user_from_session_destroy_session_variable(request)
        week_info = []

        log_extra_data = log_extra_fields(
            user_auth_id=user.id,
            request_url=request.path,
            service_type=ServiceType.API.value,
        )

        try:
            force_refresh = request.GET.get("force_refresh")
            cache_key = f"{user.email}:week-info-view-{year}-{month}"
            if cache_key in cache and not force_refresh:
                week_info = cache.get(cache_key)

            else:
                week_info = WeekInfoService.get_week_info(user, year, month)

        except Exception as e:
            logger.exception(
                f"Failed to return week info for user ID: {user.id}, "
                f"month: {month}, year: {year}.",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    request_url=request.path,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                ),
            )
            return Response(make_context(True, "Failed to return week info", week_info))

        cache.set(cache_key, week_info, timeout=settings.CACHE_TIME_OUT)
        logger.info(self.success_msg, extra=log_extra_data)

        return Response(make_context(False, self.success_msg, week_info))
