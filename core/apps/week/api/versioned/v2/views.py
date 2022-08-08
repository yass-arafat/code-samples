import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import clear_user_cache
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.user_profile.models import UserActivityLog
from core.apps.week.api.versioned.v2.schema import (
    WeekAnalysisFeedbackSchemaView,
    WeekAnalysisReportSchemaView,
)
from core.apps.week.api.versioned.v2.serializers import WeekAnalysisReportSerializer
from core.apps.week.models import WeekAnalysis
from core.apps.week.services import WeekAnalysisFeedbackService

logger = logging.getLogger(__name__)


class WeekAnalysisReportView(APIView):
    """Shows the week analysis report for users"""

    success_msg = "Week analysis report returned successfully"
    error_msg = "Could not retrieve week analysis report"

    @swagger_auto_schema(
        request_schema=WeekAnalysisReportSchemaView.request_schema,
        response=WeekAnalysisReportSchemaView.responses,
    )
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        week_analysis_code = request.GET.get("id")

        force_refresh = bool(request.GET.get("force_refresh") == "true")
        cache_key = f"{user.email}:v2:week-analysis-report:{week_analysis_code}"

        if cache_key in cache and not force_refresh:
            week_analysis_report = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, week_analysis_report))

        try:
            week_analysis = WeekAnalysis.objects.filter_active(
                user_id=user.code, code=week_analysis_code
            ).last()
            week_analysis_report = WeekAnalysisReportSerializer(week_analysis).data
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_auth_id=user.id,
                    user_id=user.code,
                    service_type=ServiceType.API.value,
                ),
            )
            return Response(
                make_context(True, self.error_msg, None),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        cache.set(cache_key, week_analysis_report, timeout=settings.CACHE_TIME_OUT)

        return Response(
            make_context(False, self.success_msg, week_analysis_report),
            status=status.HTTP_200_OK,
        )


class WeekAnalysisFeedbackView(APIView):
    """Saved the week analysis feedback for users"""

    success_msg = "Week analysis feedback saved successfully"
    error_msg = "Could not save week analysis feedback"

    @swagger_auto_schema(
        request_body=WeekAnalysisFeedbackSchemaView.request_schema,
        responses=WeekAnalysisFeedbackSchemaView.responses,
    )
    def post(self, request):
        """Gets the week analysis feedback data"""
        user = get_user_from_session_destroy_session_variable(request)

        try:
            WeekAnalysisFeedbackService(
                user, request.data
            ).save_weekly_analysis_feedback()

            response = make_context(False, self.success_msg, None)
            response_code = status.HTTP_200_OK
            clear_user_cache(user)
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_auth_id=user.id,
                    user_id=user.code,
                    service_type=ServiceType.API.value,
                ),
            )
            response = make_context(True, self.error_msg, None)
            response_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        activity_code = UserActivityLog.ActivityCode.WEEK_ANALYSIS_FEEDBACK
        return PillarResponse(
            user, request, response, activity_code, status=response_code
        )
