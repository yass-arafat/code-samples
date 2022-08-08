import logging
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import get_user_current_goal_type, pro_feature
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.plan.enums.goal_type_enum import GoalTypeEnum

from .dictionary import (
    get_freshness_overview_dict,
    get_performance_overview_dict,
    get_performance_stats_dict,
    get_prs_overview_dict,
    get_threshold_overview_dict,
    get_training_load_overview_dict,
)
from .schema import (
    FreshnessGraphApiSchemaView,
    FreshnessOverviewV2ApiSchemaView,
    LoadGraphApiSchemaView,
    PrsGraphApiSchemaView,
    StatsGraphApiSchemaView,
    ThresholdGraphApiSchemaView,
    ThresholdOverviewV2ApiSchemaView,
    TimeInZoneGraphApiSchemaView,
    TimeInZoneOverviewV2ApiSchemaView,
    TrainingLoadOverviewV2ApiSchemaView,
    ZoneDifficultyLevelOverviewV2ApiSchemaView,
)
from .services import (
    FreshnessGraphService,
    LoadGraphService,
    PerformanceFreshnessServices,
    PerformancePrsServices,
    PerformanceThresholdServices,
    PerformanceTrainingLoadServices,
    PrsGraphService,
    StatsGraphService,
    ThresholdGraphService,
    TimeInZoneGraphService,
    TimeInZoneOverviewService,
    WeekEvaluationServices,
    ZoneDifficultyLevelOverviewService,
)

logger = logging.getLogger(__name__)


class PerformanceOverviewViewV2(generics.GenericAPIView):
    def get(self, request):
        success_message = "Returned Performance Overview Successfully"
        error_message = "Failed to fetch performance overview data"
        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:" + "performance_overview"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = WeekEvaluationServices.get_performance_overview(
                user_auth, request.session["user_subscription_status"]
            )
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.error(f"{error_message}. Exception: {str(e)}")

            response_data = get_performance_overview_dict()
            return Response(make_context(True, error_message, response_data))


class PerformanceStatsViewV2(generics.GenericAPIView):
    def get(self, request):
        success_message = "Returned Performance Stats Successfully"
        error_message = "Failed to fetch performance stats data"
        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:" + "performance_stats"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = WeekEvaluationServices.get_performance_stats(user_auth)
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.error(f"{error_message}. Exception: {str(e)}")

            response_data = get_performance_stats_dict()
            return Response(make_context(True, error_message, response_data))


class PrsOverviewViewV2(generics.GenericAPIView):
    @pro_feature
    def get(self, request):
        success_message = "Returned PRS Overview Successfully"
        error_message = "Failed to fetch prs overview data"
        package_type_goal_message = "PRS overview is not shown for package type goals"
        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            if get_user_current_goal_type(user_auth) == GoalTypeEnum.PACKAGE.value:
                return Response(make_context(False, package_type_goal_message, None))

            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:" + "prs_overview"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = PerformancePrsServices.get_prs_overview(user_auth)
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.exception(f"{error_message}. Exception: {str(e)}")

            response_data = get_prs_overview_dict()
            return Response(make_context(True, error_message, response_data))


class FreshnessOverviewViewV2(generics.GenericAPIView):
    @swagger_auto_schema(responses=FreshnessOverviewV2ApiSchemaView.responses)
    @pro_feature
    def get(self, request):
        success_message = "Returned Freshness Overview Successfully"
        error_message = "Failed to fetch freshness overview data"
        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:" + "freshness_overview"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = PerformanceFreshnessServices.get_freshness_overview(
                user_auth
            )
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.error(f"{error_message}. Exception: {str(e)}")

            response_data = get_freshness_overview_dict()
            return Response(make_context(True, error_message, response_data))


class TrainingLoadOverviewViewV2(generics.GenericAPIView):
    @swagger_auto_schema(responses=TrainingLoadOverviewV2ApiSchemaView.responses)
    @pro_feature
    def get(self, request):
        success_message = "Returned Training Load Overview Successfully"
        error_message = "Failed to fetch training load overview data"
        try:
            user_auth = get_user_from_session_destroy_session_variable(request)
            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:" + "training_load_overview"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = PerformanceTrainingLoadServices.get_training_load_overview(
                user_auth
            )
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.error(f"{error_message}. Exception: {str(e)}")

            response_data = get_training_load_overview_dict()
            return Response(make_context(True, error_message, response_data))


class ThresholdOverviewViewV2(generics.GenericAPIView):
    @swagger_auto_schema(responses=ThresholdOverviewV2ApiSchemaView.responses)
    @pro_feature
    def get(self, request):
        success_message = "Returned Threshold Overview Successfully"
        error_message = "Failed to fetch threshold overview data"
        user_auth = get_user_from_session_destroy_session_variable(request)
        try:
            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:" + "threshold_overview"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            response_data = PerformanceThresholdServices.get_threshold_overview(
                user_auth
            )
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)

            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.exception(
                error_message,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_auth_id=user_auth.id,
                    service_type=ServiceType.API.value,
                ),
            )

            response_data = get_threshold_overview_dict()
            return Response(make_context(True, error_message, response_data))


class TimeInZoneOverviewViewV2(generics.GenericAPIView):
    @swagger_auto_schema(responses=TimeInZoneOverviewV2ApiSchemaView.responses)
    @pro_feature
    def get(self, request):
        success_message = "Returned Time in Zone Overview Successfully"
        error_message = "Failed to fetch Time in Zone Overview data"
        user_auth = get_user_from_session_destroy_session_variable(request)
        log_extra_args = log_extra_fields(
            user_auth_id=user_auth.id,
            service_type=ServiceType.API.value,
            request_url=request.path,
        )
        try:
            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:time_in_zone_overview"

            if cache_key in cache and not force_refresh:
                logger.info("Data already cached", extra=log_extra_args)
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            logger.info(
                "Data not cached. Fetching time in zone overview", extra=log_extra_args
            )
            response_data = TimeInZoneOverviewService(
                user_auth, log_extra_args
            ).get_time_in_zone_overview()
            logger.info(
                "Successfully retrieved time in zone overview data",
                extra=log_extra_args,
            )

            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)
            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.exception(
                error_message,
                extra=log_extra_fields(
                    user_auth_id=user_auth.id,
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                    exception_message=str(e),
                ),
            )
            return Response(make_context(True, error_message, None), status=500)


class ZoneDifficultyLevelOverviewViewV2(generics.GenericAPIView):
    @swagger_auto_schema(responses=ZoneDifficultyLevelOverviewV2ApiSchemaView.responses)
    @pro_feature
    def get(self, request):
        success_message = "Returned Zone Difficulty Level Overview Successfully"
        error_message = "Failed to fetch Zone Difficulty Level Overview data"
        user_auth = get_user_from_session_destroy_session_variable(request)
        log_extra_args = log_extra_fields(
            user_auth_id=user_auth.id,
            service_type=ServiceType.API.value,
            request_url=request.path,
        )
        try:
            force_refresh = request.GET.get("force_refresh") == "true"
            cache_key = user_auth.email + ":v2:zone_difficulty_level_overview"

            if cache_key in cache and not force_refresh:
                logger.info("Data already cached", extra=log_extra_args)
                cached_data = cache.get(cache_key)
                return Response(make_context(False, success_message, cached_data))

            logger.info(
                "Data not cached. Fetching zone difficulty level overview",
                extra=log_extra_args,
            )
            response_data = ZoneDifficultyLevelOverviewService(
                user_auth, log_extra_args
            ).get_zone_difficulty_level_overview()
            logger.info(
                "Successfully retrieved zone difficulty level overview data",
                extra=log_extra_args,
            )

            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)
            return Response(make_context(False, success_message, response_data))
        except Exception as e:
            logger.exception(
                error_message,
                extra=log_extra_fields(
                    user_auth_id=user_auth.id,
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                    exception_message=str(e),
                ),
            )
            return Response(make_context(True, error_message, None), status=500)


class StatsGraphApiView(APIView):
    success_msg = "Stats graph data returned successfully."
    error_msg = "Could not load graph data. Error: {0}"

    @swagger_auto_schema(responses=StatsGraphApiSchemaView.responses)
    def get(self, request, year):
        user = get_user_from_session_destroy_session_variable(request)
        year_start_date = datetime(year, 1, 1)
        year_end_date = datetime(year, 12, 31)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = f"{user.email}:stats_graph_v2{year}-{year}"

        if cache_key in cache and not force_refresh:
            graph_data = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, graph_data))
        else:
            try:
                stats_service = StatsGraphService(user, year_start_date, year_end_date)
                graph_data = stats_service.graph_data()
            except Exception as e:
                logger.error(self.error_msg.format(str(e)) + ". Exception: {str(e)}")
                return Response(True, self.error_msg.format(str(e)), None)
            cache.set(cache_key, graph_data, timeout=settings.CACHE_TIME_OUT)
        return Response(make_context(False, self.success_msg, graph_data))


class PrsGraphApiView(APIView):
    success_msg = "PRS graph data returned successfully."
    error_msg = "Could not fetch PRS graph data"

    @swagger_auto_schema(responses=PrsGraphApiSchemaView.responses)
    @pro_feature
    def get(self, request, year):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = f"{user.email}:prs_graph_v2{year}"

        if cache_key in cache and not force_refresh:
            prs_graph_data = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, prs_graph_data))

        try:
            prs_service = PrsGraphService(user, year)
            prs_graph_data = prs_service.graph_data()
        except Exception as e:
            logger.error(self.error_msg + f". Exception: {str(e)}")
            return Response(True, self.error_msg, None)

        cache.set(cache_key, prs_graph_data, timeout=settings.CACHE_TIME_OUT)
        return Response(make_context(False, self.success_msg, prs_graph_data))


class FreshnessGraphApiView(APIView):
    success_msg = "Freshness graph data returned successfully."
    error_msg = "Could not fetch freshness graph data"

    @swagger_auto_schema(responses=FreshnessGraphApiSchemaView.responses)
    @pro_feature
    def get(self, request, year):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = f"{user.email}:freshness_graph_v2{year}"

        if cache_key in cache and not force_refresh:
            freshness_graph_data = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, freshness_graph_data))

        try:
            freshness_service = FreshnessGraphService(user, year)
            freshness_graph_data = freshness_service.graph_data()
        except Exception as e:
            logger.error(self.error_msg + f". Exception: {str(e)}")
            return Response(True, self.error_msg, None)

        cache.set(cache_key, freshness_graph_data, timeout=settings.CACHE_TIME_OUT)
        return Response(make_context(False, self.success_msg, freshness_graph_data))


class LoadGraphApiView(APIView):
    success_msg = "Load graph data returned successfully."
    error_msg = "Could not load graph data. Error: {0}"

    @swagger_auto_schema(responses=LoadGraphApiSchemaView.responses)
    @pro_feature
    def get(self, request, year):
        user = get_user_from_session_destroy_session_variable(request)
        first_date = datetime(year, 1, 1)
        last_date = datetime(year, 12, 31)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = f"{user.email}:load_graph_v2{year}-{year}"

        if cache_key in cache and not force_refresh:
            graph_data = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, graph_data))
        else:
            try:
                load_service = LoadGraphService(user, first_date, last_date)
                graph_data = load_service.graph_data()
            except Exception as e:
                logger.error(self.error_msg.format(str(e)) + ". Exception: {str(e)}")
                return Response(True, self.error_msg.format(str(e)), None)
            cache.set(cache_key, graph_data, timeout=settings.CACHE_TIME_OUT)
        return Response(make_context(False, self.success_msg, graph_data))


class ThresholdGraphApiView(APIView):
    success_msg = "Threshold graph data returned successfully."
    error_msg = "Could not threshold graph data."

    @swagger_auto_schema(responses=ThresholdGraphApiSchemaView.responses)
    @pro_feature
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = f"{user.email}:threshold_graph_v2{start_date}-{end_date}"
        if cache_key in cache and not force_refresh:
            graph_data = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, graph_data))

        try:
            threshold_service = ThresholdGraphService(user, start_date, end_date)
            graph_data = threshold_service.get_graph_data()
            cache.set(cache_key, graph_data, timeout=settings.CACHE_TIME_OUT)
            return Response(make_context(False, self.success_msg, graph_data))
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
            return Response(make_context(True, self.error_msg, None))


class TimeInZoneGraphApiView(APIView):
    success_msg = "Time in zone graph data returned successfully."
    error_msg = "Failed to fetch time in zone graph data."

    @swagger_auto_schema(responses=TimeInZoneGraphApiSchemaView.responses)
    @pro_feature
    def get(self, request, year):
        user = get_user_from_session_destroy_session_variable(request)
        log_extra_args = log_extra_fields(
            user_auth_id=user.id,
            service_type=ServiceType.API.value,
            request_url=request.path,
        )

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = f"{user.email}:time_in_zone_graph_v2-{year}"

        if cache_key in cache and not force_refresh:
            logger.info("Data already cached", extra=log_extra_args)
            graph_data = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, graph_data))

        try:
            logger.info(
                "Data not cached. Fetching time in zone graph", extra=log_extra_args
            )
            graph_data = TimeInZoneGraphService(user, year, log_extra_args).graph_data()
            logger.info(
                "Successfully retrieved time in zone graph data", extra=log_extra_args
            )
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                    exception_message=str(e),
                ),
            )
            return Response(True, self.error_msg, None)
        cache.set(cache_key, graph_data, timeout=settings.CACHE_TIME_OUT)
        return Response(make_context(False, self.success_msg, graph_data))
