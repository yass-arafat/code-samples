from datetime import date

from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    make_context,
)

from ...services import UserDailyEvaluation


@api_view(["GET"])
def get_daily_prs_over_time(request):
    user = get_user_from_session_destroy_session_variable(request)

    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_daily_prs_over_time"

    if cache_key in cache and not force_refresh:
        daily_prs_dict = cache.get(cache_key)
    else:
        daily_prs_dict = UserDailyEvaluation.get_daily_prs(user, date.today())
        cache.set(cache_key, daily_prs_dict, timeout=settings.CACHE_TIME_OUT)

    return Response(
        make_context(False, "Daily PRS returned successfully", daily_prs_dict)
    )


@api_view(["GET"])
def prs_graph_view(request):
    user = get_user_from_session_destroy_session_variable(request)

    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_daily_prs_over_time"

    if cache_key in cache and not force_refresh:
        daily_prs_dict = cache.get(cache_key)
    else:
        daily_prs_dict = UserDailyEvaluation.get_prs_graph(user, date.today())
        cache.set(cache_key, daily_prs_dict, timeout=settings.CACHE_TIME_OUT)

    return Response(
        make_context(False, "Daily PRS returned successfully", daily_prs_dict)
    )


@api_view(["GET"])
def get_planned_load_over_time(request):
    user = get_user_from_session_destroy_session_variable(request)
    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_planned_load_over_time"

    if cache_key in cache and not force_refresh:
        load_graph_dict = cache.get(cache_key)
    else:
        try:
            load_graph_dict = UserDailyEvaluation.get_load_graph_data(user)
        except Exception as e:
            return Response(make_context(True, str(e), None))
        cache.set(cache_key, load_graph_dict, timeout=settings.CACHE_TIME_OUT)
    return Response(
        make_context(False, "Load graph data returned successfully", load_graph_dict)
    )


@api_view(["GET"])
def get_last_seven_days_recovery_index(request):
    user = get_user_from_session_destroy_session_variable(request)
    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_last_seven_days_recovery_index"

    if cache_key in cache and not force_refresh:
        seven_days_ri_dict = cache.get(cache_key)
    else:
        seven_days_ri_dict = UserDailyEvaluation.get_last_seven_days_recovery_index(
            user, date.today()
        )
        cache.set(cache_key, seven_days_ri_dict, timeout=settings.CACHE_TIME_OUT)
    return Response(
        make_context(
            False,
            "Last Seven Days recovery Index data returned successfully",
            seven_days_ri_dict,
        )
    )


@api_view(["GET"])
def get_last_seven_days_sqs(request):
    user = get_user_from_session_destroy_session_variable(request)
    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_last_seven_days_sqs"

    if cache_key in cache and not force_refresh:
        seven_days_sqs_dict = cache.get(cache_key)
    else:
        seven_days_sqs_dict = UserDailyEvaluation.get_last_seven_days_sqs(
            user, date.today()
        )
        cache.set(cache_key, seven_days_sqs_dict, timeout=settings.CACHE_TIME_OUT)
    return Response(
        make_context(
            False, "Last Seven Days sqs data returned successfully", seven_days_sqs_dict
        )
    )


@api_view(["GET"])
def get_last_seven_days_sas(request):
    user = get_user_from_session_destroy_session_variable(request)
    force_refresh = True if request.GET.get("force_refresh") == "true" else False
    cache_key = user.email + ":" + "get_last_seven_days_sas"

    if cache_key in cache and not force_refresh:
        sas_graph = cache.get(cache_key)
    else:
        sas_graph = UserDailyEvaluation.get_last_seven_days_sas(user, date.today())
        cache.set(cache_key, sas_graph, timeout=settings.CACHE_TIME_OUT)
    return Response(
        make_context(False, "Last Seven Days SAS data returned successfully", sas_graph)
    )
