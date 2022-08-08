import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import has_pro_feature_access
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.home.api.versioned.v2.schema import (
    HomePageBaseSchemaView,
    RecentRideSchemaView,
    TryGoalSchemaView,
    WeeklyStatsSchemaView,
)
from core.apps.home.services import HomePageService, RecentRideService

logger = logging.getLogger(__name__)


class RecentRideView(APIView):
    """Shows the achieved personal record badges"""

    success_msg = "Recent ride data returned successfully"
    error_msg = "Could not retrieve recent ride data"

    @swagger_auto_schema(responses=RecentRideSchemaView.responses)
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":v2:" + "recent_ride"

        if cache_key in cache and not force_refresh:
            recent_ride_data = cache.get(cache_key)
            response = make_context(False, self.success_msg, recent_ride_data)
        else:
            try:
                recent_ride_data = RecentRideService.get_recent_ride_data(user)
            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            cache.set(cache_key, recent_ride_data, timeout=settings.CACHE_TIME_OUT)
            response = make_context(False, self.success_msg, recent_ride_data)

        return Response(response, status=status.HTTP_200_OK)


class HomePageBaseView(APIView):
    """Shows the achieved personal record badges"""

    success_msg = "Base home page data returned successfully"
    error_msg = "Could not retrieve base home data"

    @swagger_auto_schema(responses=HomePageBaseSchemaView.response)
    def get(self, request):

        user = get_user_from_session_destroy_session_variable(request)
        pro_feature_access = has_pro_feature_access(
            request.session["user_subscription_status"]
        )

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":v2:" + "base_home_page"

        if cache_key in cache and not force_refresh:
            base_home_page_data = cache.get(cache_key)
            response = make_context(False, self.success_msg, base_home_page_data)
        else:
            try:
                base_home_page_data = HomePageService.get_base_home_page_data(
                    user, pro_feature_access
                )
            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            cache.set(cache_key, base_home_page_data, timeout=settings.CACHE_TIME_OUT)
            response = make_context(False, self.success_msg, base_home_page_data)

        return Response(response, status=status.HTTP_200_OK)


class TryGoalView(APIView):
    """Shows the achieved personal record badges"""

    success_msg = "Try a goal event list returned successfully"
    error_msg = "Could not retrieve try a goal event list"

    @swagger_auto_schema(responses=TryGoalSchemaView.response)
    def get(self, request):

        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":v2:" + "home_page_goal_list"  # change

        if cache_key in cache and not force_refresh:
            goal_data = cache.get(cache_key)
            response = make_context(False, self.success_msg, goal_data)
        else:
            try:
                home_page_event_data = HomePageService.get_home_page_event_list(user)
            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            cache.set(cache_key, home_page_event_data, timeout=settings.CACHE_TIME_OUT)
            response = make_context(False, self.success_msg, home_page_event_data)

        return Response(response, status=status.HTTP_200_OK)


class WeeklyStatsView(APIView):
    """Shows the achieved personal record badges"""

    success_msg = "Weekly stats returned successfully"
    error_msg = "Could not retrieve weekly stats"

    @swagger_auto_schema(responses=WeeklyStatsSchemaView.response)
    def get(self, request):

        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":v2:" + "home_page_weekly_stats"  # change

        if cache_key in cache and not force_refresh:
            weekly_stats_data = cache.get(cache_key)
            response = make_context(False, self.success_msg, weekly_stats_data)
        else:
            try:
                weekly_stats = HomePageService.get_weekly_stats(user)
            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            cache.set(cache_key, weekly_stats, timeout=settings.CACHE_TIME_OUT)
            response = make_context(False, self.success_msg, weekly_stats)

        return Response(response, status=status.HTTP_200_OK)
