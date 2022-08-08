import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.achievements.api.versioned.v2.schema import (
    AchievementOverviewSchemaView,
    PersonalRecordSchemaView,
    RecordDetailSchemaView,
)
from core.apps.achievements.services import AchievementService
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)

logger = logging.getLogger(__name__)


class AchievementOverviewView(APIView):
    """Shows the achieved personal record badges"""

    success_msg = "Achievement overview data returned successfully"
    error_msg = "Could not retrieve achievement overview data"

    @swagger_auto_schema(responses=AchievementOverviewSchemaView.responses)
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = f"{user.email}:achievement-overview"

        if cache_key in cache and not force_refresh:
            achievements = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, achievements))
        else:
            try:
                achievements = AchievementService.get_achievement_overview(user)
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
            cache.set(cache_key, achievements, timeout=settings.CACHE_TIME_OUT)

        return Response(
            make_context(False, self.success_msg, achievements),
            status=status.HTTP_200_OK,
        )


class PersonalRecordView(APIView):
    """Shows the summary of the all achieved personal records"""

    success_msg = "Personal record summary returned successfully"
    error_msg = "Could not retrieve personal record summary"

    @swagger_auto_schema(responses=PersonalRecordSchemaView.responses)
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = f"{user.email}:personal-record"

        if cache_key in cache and not force_refresh:
            personal_records = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, personal_records))
        else:
            try:
                personal_records = AchievementService.get_personal_records(user)
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
            cache.set(cache_key, personal_records, timeout=settings.CACHE_TIME_OUT)

        return Response(
            make_context(False, self.success_msg, personal_records),
            status=status.HTTP_200_OK,
        )


class RecordDetailView(APIView):
    """Shows the details and history of a specific personal record"""

    success_msg = "Personal record detail returned successfully"
    error_msg = "Could not retrieve personal record detail"

    @swagger_auto_schema(
        request_body=RecordDetailSchemaView.request_schema,
        responses=RecordDetailSchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        record_type = request.data.get("record_type", False)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = f"{user.email}:record-detail-of-type:{record_type}"

        if cache_key in cache and not force_refresh:
            record_detail = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, record_detail))
        else:
            try:
                record_detail = AchievementService.get_record_detail(user, record_type)
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
            cache.set(cache_key, record_detail, timeout=settings.CACHE_TIME_OUT)

        return Response(
            make_context(False, self.success_msg, record_detail),
            status=status.HTTP_200_OK,
        )
