from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    make_context,
)

from ...services import UserBlockEvaluation


# Depreciated from R7
@api_view(["GET"])
def get_training_blocks_over_time(request):
    user = get_user_from_session_destroy_session_variable(request)
    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_training_blocks_over_time"
    if cache_key in cache and not force_refresh:
        training_blocks_dict = cache.get(cache_key)
    else:
        training_blocks_dict = UserBlockEvaluation.get_training_block_details(user)
        cache.set(cache_key, training_blocks_dict, timeout=settings.CACHE_TIME_OUT)
    return Response(
        make_context(
            False,
            "User Training Block evaluation load graph data returned successfully",
            training_blocks_dict,
        )
    )


class TrainingBlocksView(APIView):
    """Returns block details to performance page"""

    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":" + "get_training_blocks_over_time"
        if cache_key in cache and not force_refresh:
            training_blocks_dict = cache.get(cache_key)
        else:
            training_blocks_dict = UserBlockEvaluation.training_block_details(user)
            cache.set(cache_key, training_blocks_dict, timeout=settings.CACHE_TIME_OUT)
        return Response(
            make_context(
                False,
                "User Training Block evaluation load graph data returned successfully",
                training_blocks_dict,
            )
        )
