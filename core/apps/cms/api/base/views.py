from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView

from core.apps.common.common_functions import cache_data, pillar_response

from ...services import get_information_detail, get_information_sections


class InformationSectionView(APIView):
    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        response_data = get_information_sections()
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)
        return response_data


class InformationDetailView(APIView):
    @cache_data
    @pillar_response()
    def get(self, request, info_detail_id, **kwargs):
        response_data = get_information_detail(info_detail_id)
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)
        return response_data
