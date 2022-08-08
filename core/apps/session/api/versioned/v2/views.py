import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import clear_user_cache, has_pro_feature_access
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.evaluation.session_evaluation.utils import get_actual_session
from core.apps.user_profile.models import UserActivityLog

from .dictionary import get_sessions_overview_dict
from .schema import SessionFeedbackSchemaView
from .services import SessionDetailService, SessionService

logger = logging.getLogger(__name__)


class SessionsOverviewViewV2(generics.GenericAPIView):
    def get(self, request):
        success_message = "Returned Sessions Overview Successfully"
        error_message = "Failed to fetch sessions overview data"
        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = user_auth.email + ":v2:" + "sessions_overview"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = SessionService.get_sessions_overview(user_auth)
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.error(f"{error_message}. Exception: {str(e)}")

            response_data = get_sessions_overview_dict()
            return Response(make_context(True, error_message, response_data))


class SessionDetailView(APIView):
    def post(self, request):
        """Returns the detail of a session to the detail and evaluation page of the app"""
        user = get_user_from_session_destroy_session_variable(request)
        pro_feature_access = has_pro_feature_access(
            request.session["user_subscription_status"]
        )

        try:
            planned_id = request.data.get("planned_id")
            actual_id = request.data.get("actual_id")

            if not (actual_id or planned_id):
                return Response(make_context(True, "No session id is provided", None))

            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = (
                user.email
                + ":"
                + "get_session_details_data"
                + "-"
                + str(planned_id)
                + "-"
                + str(actual_id)
            )

            if cache_key in cache and not force_refresh:
                session_data_dict = cache.get(cache_key)
            else:
                session_data_dict = SessionDetailService().get_session_details(
                    user, planned_id, actual_id, pro_feature_access
                )
                if session_data_dict is None:
                    return Response(
                        make_context(True, "No session found for this id", None)
                    )
                cache.set(cache_key, session_data_dict, timeout=settings.CACHE_TIME_OUT)
            return Response(
                make_context(False, "Session retrieved successfully", session_data_dict)
            )
        except Exception as e:
            logger.exception(
                "Failed to retrieve Session.",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    request_url=request.path,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                ),
            )
            return Response(make_context(True, "Failed to retrieve Session", None))


class SessionFeedbackView(APIView):
    session_feedback_activity_code = UserActivityLog.ActivityCode.USER_SESSION_FEEDBACK

    @swagger_auto_schema(
        request_body=SessionFeedbackSchemaView.request_schema,
        responses=SessionFeedbackSchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        session_metadata = request.data.get("session_metadata")
        effort_level = request.data.get("effort_level")
        session_followed_as_planned = request.data.get("session_followed_as_planned")
        reason = request.data.get("reason")
        explanation = request.data.get("explanation")
        actual_id = session_metadata["actual_id"] if session_metadata else None

        if not actual_id:
            msg = "No actual id was found in request"
            logger.exception(
                msg,
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            response = make_context(True, msg, None)
            return PillarResponse(
                user, request, response, self.session_feedback_activity_code
            )

        try:
            actual_session = get_actual_session(user, actual_id)
            if not actual_session:
                msg = "No actual session was found for this id"
                logger.exception(
                    msg,
                    extra=log_extra_fields(
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                        request_url=request.path,
                    ),
                )
                response = make_context(True, msg, None)
                return PillarResponse(
                    user, request, response, self.session_feedback_activity_code
                )

            session_metadata = SessionService.save_session_feedback(
                actual_session,
                effort_level,
                session_followed_as_planned,
                reason,
                explanation,
            )
            clear_user_cache(user)
            logger.info(
                f"Session feedback for actual id: {session_metadata['actual_id']} is saved successfully"
            )
            response = make_context(
                False, "Session feedback saved successfully", session_metadata
            )
            return PillarResponse(
                user, request, response, self.session_feedback_activity_code
            )

        except Exception as e:
            msg = "Could not save session feedback"
            logger.exception(
                msg,
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            response = make_context(True, msg, None)
            return PillarResponse(
                user, request, response, self.session_feedback_activity_code
            )
