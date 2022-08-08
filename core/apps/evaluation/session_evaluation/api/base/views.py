import logging

from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import has_pro_feature_access
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)

from ...services import PlannedSessionEvaluation

logger = logging.getLogger(__name__)


@api_view(["GET"])
def get_session_graph_data_with_threshold(request):
    user = get_user_from_session_destroy_session_variable(request)
    session_id = request.GET.get("session_id")
    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    time_interval = request.GET.get("time_interval")
    total_point = request.GET.get("total_point")
    integer_value = request.GET.get("integer_value")

    cache_key = user.email + ":" + "graph_data_with_threshold" + str(session_id)

    if time_interval:
        cache_key = cache_key + "-" + time_interval
        time_interval = int(time_interval)
    if total_point:
        cache_key = cache_key + "-" + total_point
        total_point = int(total_point)
    if integer_value == "true":
        cache_key = cache_key + "-" + integer_value
        integer_value = True
    else:
        cache_key = cache_key + "-" + integer_value
        integer_value = False

    if cache_key in cache and not force_refresh:
        session_graph_data_dict = cache.get(cache_key)
    else:
        session_graph_data_dict = (
            PlannedSessionEvaluation.get_session_graph_data_with_threshold(
                user, session_id, total_point
            )
        )

        cache.set(cache_key, session_graph_data_dict, timeout=settings.CACHE_TIME_OUT)
    return Response(make_context(False, "", session_graph_data_dict))


@api_view(["GET"])
def get_session_details_data(request):
    user = get_user_from_session_destroy_session_variable(request)
    session_id = request.GET.get("session_id", False)

    if not session_id:
        return Response(make_context(True, "No session id is provided", None))

    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_session_details_data" + "-" + str(session_id)

    if cache_key in cache and not force_refresh:
        session_graph_data_dict = cache.get(cache_key)
    else:
        session_graph_data_dict = PlannedSessionEvaluation.get_session_graph_other_data(
            user, session_id
        )
        cache.set(cache_key, session_graph_data_dict, timeout=settings.CACHE_TIME_OUT)
    if session_graph_data_dict is None:
        return Response(make_context(True, "No session found for this id", None))
    return Response(
        make_context(False, "Session retrieved successfully.", session_graph_data_dict)
    )


class SessionEvaluationDetailsView(APIView):
    """Returns session details to performance page"""

    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        planned_id = request.data.get("planned_id", False)
        actual_id = request.data.get("actual_id", False)

        if not (actual_id or planned_id):
            return Response(make_context(True, "No session id is provided", None))

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = (
            user.email
            + ":"
            + "get_session_details_data"
            + "-"
            + str(planned_id)
            + str(actual_id)
        )

        if cache_key in cache and not force_refresh:
            session_graph_data_dict = cache.get(cache_key)
        else:
            session_graph_data_dict = (
                PlannedSessionEvaluation.get_session_graph_other_data(
                    user, planned_id, actual_id
                )
            )
            cache.set(
                cache_key, session_graph_data_dict, timeout=settings.CACHE_TIME_OUT
            )
        if session_graph_data_dict is None:
            return Response(make_context(True, "No session found for this id", None))
        return Response(
            make_context(
                False, "Session retrieved successfully.", session_graph_data_dict
            )
        )


class SessionGraphDataView(APIView):
    """Returns the graph data of a session"""

    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        pro_feature_access = has_pro_feature_access(
            request.session["user_subscription_status"]
        )
        try:
            # If the user doesn't have pro feature access, then we won't show any
            # planned session related data
            planned_id = request.data.get("planned_id") if pro_feature_access else None
            actual_id = request.data.get("actual_id")
            force_refresh = request.GET.get("force_refresh") == "true"
            total_point = int(request.GET.get("total_point", 250))

            cache_key = (
                user.email
                + ":graph_data_with_threshold"
                + str(planned_id)
                + str(actual_id)
            )

            if total_point:
                cache_key = cache_key + "-" + str(total_point)
                total_point = int(total_point)

            if cache_key in cache and not force_refresh:
                session_graph_data_dict = cache.get(cache_key)
            else:
                session_graph_data_dict = (
                    PlannedSessionEvaluation.get_session_graph_data_with_threshold(
                        user, planned_id, total_point, actual_id
                    )
                )
                cache.set(
                    cache_key, session_graph_data_dict, timeout=settings.CACHE_TIME_OUT
                )

            return Response(make_context(False, "", session_graph_data_dict))
        except Exception as e:
            logger.exception(
                "Failed to serve session evaluation graph",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    request_url=request.path,
                    service_type=ServiceType.API.value,
                    exception_message=str(e),
                ),
            )
            return Response(
                make_context(True, "Failed to load session graph", None), status=500
            )
