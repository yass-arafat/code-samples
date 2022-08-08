import datetime
import logging

from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import pro_feature
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.enums.date_time_format_enum import DateTimeFormatEnum
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    make_context,
)

from ...services import UserDailyServices

logger = logging.getLogger(__name__)


@api_view(["GET"])
def get_today_details_data(request):  # Deprecated
    user_auth = get_user_from_session_destroy_session_variable(request)

    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user_auth.email + ":" + "get_today_details_data"

    if cache_key in cache and not force_refresh:
        cached_data = cache.get(cache_key)
        return Response(
            make_context(False, "Today data returned successfully", cached_data)
        )
    else:
        timezone_offset = user_auth.timezone_offset
        user_local_date = DateTimeUtils.get_user_local_date_time_from_utc(
            timezone_offset, datetime.datetime.now()
        ).strftime(DateTimeFormatEnum.app_date_format.value)

        today_details = UserDailyServices.get_today_details(
            user_auth, datetime.date.today(), user_local_date
        )
        cache.set(cache_key, today_details, timeout=settings.CACHE_TIME_OUT)

    return Response(
        make_context(False, "Today data returned successfully", today_details)
    )


class TodayDetailsView(APIView):
    """Returns today details, past and upcoming rides in home page"""

    @pro_feature
    def get(self, request):
        user_auth = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user_auth.email + ":" + "get_today_details_data"

        if cache_key in cache and not force_refresh:
            cached_data = cache.get(cache_key)
            return Response(
                make_context(False, "Today data returned successfully", cached_data)
            )
        else:
            today_details = UserDailyServices.today_details(user_auth)
            cache.set(cache_key, today_details, timeout=settings.CACHE_TIME_OUT)

        return Response(
            make_context(False, "Today data returned successfully", today_details)
        )
