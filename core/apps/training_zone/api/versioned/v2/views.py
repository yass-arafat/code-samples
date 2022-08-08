import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.response import Response

from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)

from .dictionary import get_training_zone_dictionary
from .schema import TrainingZonesViewV2ApiSchemaView
from .services import TrainingZonesServices

logger = logging.getLogger(__name__)


class TrainingZonesViewV2(generics.GenericAPIView):
    @swagger_auto_schema(responses=TrainingZonesViewV2ApiSchemaView.responses)
    def get(self, request):
        user_auth = get_user_from_session_destroy_session_variable(request)

        success_message = "Returned Training Zones Successfully"
        error_message = "Failed to fetch training zones data"
        try:
            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = user_auth.email + ":v2:" + "training_zones"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = TrainingZonesServices.get_training_zones(user_auth)
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.exception(
                error_message,
                extra=log_extra_fields(
                    user_auth_id=user_auth.id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )

            response_data = get_training_zone_dictionary()
            return Response(make_context(True, error_message, response_data))
