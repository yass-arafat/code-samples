import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.response import Response

from core.apps.common.common_functions import has_pro_feature_access, pro_feature
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.notification.services import delete_last_today_focus_notification
from core.apps.plan.tasks import delete_goal
from core.apps.user_profile.models import UserActivityLog

from .dictionary import (
    get_event_details_dictionary,
    get_plan_overview_dictionary,
    get_plan_stats_dictionary,
)
from .schema import DeleteGoalSchemaView, GoalDetailSchemaView, PlanStatsV2SchemaView
from .services import PlanServices

logger = logging.getLogger(__name__)


class PlanOverviewViewV2(generics.GenericAPIView):
    def get(self, request):
        success_message = "Returned Plan Overview Successfully"
        error_message = "Failed to fetch plan overview data"
        basic_user_message = "Basic users can not access goal data"
        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            if not has_pro_feature_access(request.session["user_subscription_status"]):
                response_data = get_plan_overview_dictionary()
                return Response(make_context(False, basic_user_message, response_data))

            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = user_auth.email + ":v2:" + "plan_overview"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = PlanServices(user_auth).get_plan_overview()
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.error(f"{error_message}. Exception: {str(e)}")

            response_data = get_plan_overview_dictionary()
            return Response(make_context(True, error_message, response_data))


class PlanStatsViewV2(generics.GenericAPIView):
    @swagger_auto_schema(responses=PlanStatsV2SchemaView.responses)
    def get(self, request):
        success_message = "Returned Plan Stats Successfully"
        error_message = "Failed to fetch plan stats data"
        basic_user_message = "Basic users can not access goal data"

        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            if not has_pro_feature_access(request.session["user_subscription_status"]):
                response_data = get_plan_stats_dictionary()
                return Response(make_context(False, basic_user_message, response_data))

            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = user_auth.email + ":v2:" + "plan_stats"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = PlanServices(user_auth).get_plan_stats()
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.error(f"{error_message}. Exception: {str(e)}")

            response_data = get_plan_stats_dictionary()
            return Response(make_context(True, error_message, response_data))


class GoalDetailView(generics.GenericAPIView):
    @swagger_auto_schema(responses=GoalDetailSchemaView.responses)
    @pro_feature
    def get(self, request):
        success_message = "Returned goal details successfully"
        error_message = "Failed to fetch goal details"
        user_auth = get_user_from_session_destroy_session_variable(request)
        try:
            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = user_auth.email + ":v2:" + "goal_details"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = PlanServices(user_auth).get_goal_details()
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.exception(
                str(e),
                extra=log_extra_fields(
                    user_id=user_auth.code,
                    user_auth_id=user_auth.id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )

            response_data = get_event_details_dictionary()
            return Response(make_context(True, error_message, response_data))


class DeleteGoalView(generics.GenericAPIView):
    @swagger_auto_schema(responses=DeleteGoalSchemaView.responses)
    @pro_feature
    def delete(self, request):
        success_message = "Deleted current goal successfully"
        error_message = "Failed to delete current goal"
        no_user_found_message = "No user found with this credentials"

        user = get_user_from_session_destroy_session_variable(request)
        delete_goal_activity_code = UserActivityLog.ActivityCode.DELETE_GOAL
        if not user:
            logger.error(
                no_user_found_message,
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            return Response(make_context(True, no_user_found_message, None))

        try:
            delete_goal(user)

            # Deactivate last/current today focus, as after deleting a plan there is no
            # current today focus before user creates a new plan
            delete_last_today_focus_notification(user)

            response = make_context(False, success_message, None)
        except Exception as e:
            logger.exception(
                error_message,
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            response = make_context(True, error_message, None)

        return PillarResponse(user, request, response, delete_goal_activity_code)
