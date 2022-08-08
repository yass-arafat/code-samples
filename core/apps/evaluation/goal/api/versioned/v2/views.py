import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import pro_feature
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.evaluation.goal.services import (
    GoalEvaluationFreshnessGraph,
    GoalEvaluationService,
    GoalEvaluationTimeInZoneGraphService,
    GoalEvaluationTimeVsDistanceGraph,
    GoalEvaluationTrainingLoadGraph,
)

from .schema import (
    EvaluationFreshnessGraphSchemaView,
    EvaluationGoalScoresSchemaView,
    EvaluationGoalStatsSchemaView,
    EvaluationGoalSummarySchemaView,
    EvaluationTimeInZoneGraphSchemaView,
    EvaluationTimeVsDistanceGraphSchemaView,
    EvaluationTrainingLoadGraphSchemaView,
)

logger = logging.getLogger(__name__)


class EvaluationGoalSummaryView(APIView):
    """Provides summary data of evaluated goal. A goal could be event based or could be package based.
    Evaluation of goal also could be event based or package based"""

    success_msg = "Goal evaluation summary data returned successfully."
    error_msg = "Could not retrieve goal summary data."

    @swagger_auto_schema(responses=EvaluationGoalSummarySchemaView.response)
    @pro_feature
    def get(self, request):

        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":v2:" + "goal_evaluation_summary"

        if cache_key in cache and not force_refresh:
            goal_evaluation_summary_data = cache.get(cache_key)
            logger.info(
                f"Returning goal evaluation summary data from cache for user {user.code}"
            )
            response = make_context(
                False, self.success_msg, goal_evaluation_summary_data
            )
        else:
            try:
                logger.info(
                    f"Fetching goal evaluation summary data for user {user.code}"
                )
                goal_evaluation_summary_data = (
                    GoalEvaluationService.get_goal_evaluation_summary_data(user.code)
                )
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
            cache.set(
                cache_key, goal_evaluation_summary_data, timeout=settings.CACHE_TIME_OUT
            )
            response = make_context(
                False, self.success_msg, goal_evaluation_summary_data
            )

        return Response(response, status=status.HTTP_200_OK)


class EvaluationGoalStatsView(APIView):
    """Provides stats data of evaluated goal. A goal could be event based or could be package based.
    Evaluation of goal also could be event based or package based"""

    success_msg = "Goal evaluation stats data returned successfully."
    error_msg = "Could not retrieve goal stats data."

    @swagger_auto_schema(responses=EvaluationGoalStatsSchemaView.response)
    @pro_feature
    def get(self, request):

        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":v2:" + "goal_evaluation_stats"

        if cache_key in cache and not force_refresh:
            goal_evaluation_stats_data = cache.get(cache_key)
            logger.info(
                f"Returning goal evaluation stats data from cache for user {user.code}"
            )
            response = make_context(False, self.success_msg, goal_evaluation_stats_data)
        else:
            try:
                logger.info(f"Fetching goal evaluation stats data for user {user.code}")
                goal_evaluation_stats_data = GoalEvaluationService(
                    user
                ).get_goal_evaluation_stats_data()
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
            cache.set(
                cache_key, goal_evaluation_stats_data, timeout=settings.CACHE_TIME_OUT
            )
            response = make_context(False, self.success_msg, goal_evaluation_stats_data)

        return Response(response, status=status.HTTP_200_OK)


class EvaluationGoalScoresView(APIView):
    """Provides stats data of evaluated goal. A goal could be event based or could be package based.
    Evaluation of goal also could be event based or package based"""

    success_msg = "Goal evaluation scores data returned successfully."
    error_msg = "Could not retrieve goal scores data."

    @swagger_auto_schema(responses=EvaluationGoalScoresSchemaView.response)
    @pro_feature
    def get(self, request):

        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = user.email + ":v2:" + "goal_evaluation_scores"

        if cache_key in cache and not force_refresh:
            goal_evaluation_scores_data = cache.get(cache_key)
            logger.info(
                f"Returning goal evaluation scores data from cache for user {user.code}"
            )
            response = make_context(
                False, self.success_msg, goal_evaluation_scores_data
            )
        else:
            try:
                logger.info(
                    f"Fetching goal evaluation scores data for user {user.code}"
                )
                goal_evaluation_scores_data = GoalEvaluationService(
                    user
                ).get_goal_evaluation_scores_data()
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
            cache.set(
                cache_key, goal_evaluation_scores_data, timeout=settings.CACHE_TIME_OUT
            )
            response = make_context(
                False, self.success_msg, goal_evaluation_scores_data
            )

        return Response(response, status=status.HTTP_200_OK)


class EvaluationGoalTrainingLoadGraphView(APIView):
    """Provides graph of actual load and actual acute load of evaluated goal. A goal could be event based or
    could be package based. Evaluation of goal also could be event based or package based"""

    success_msg = "Goal evaluation training load graph returned successfully."
    error_msg = "Could not retrieve goal training load graph."

    @swagger_auto_schema(responses=EvaluationTrainingLoadGraphSchemaView.response)
    @pro_feature
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = user.email + ":v2:" + "goal_evaluation_training_load_graph"

        if cache_key in cache and not force_refresh:
            training_load_graph = cache.get(cache_key)
            logger.info(
                f"Returning goal evaluation training load graph from cache for user {user.code}"
            )
            response = make_context(False, self.success_msg, training_load_graph)
            return Response(response)

        try:
            logger.info(f"Fetching goal evaluation training load for user {user.code}")
            training_load_graph = GoalEvaluationTrainingLoadGraph(user).get_graph_data()

            cache.set(cache_key, training_load_graph, timeout=settings.CACHE_TIME_OUT)
            response = make_context(False, self.success_msg, training_load_graph)
            return Response(response)
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


class EvaluationGoalFreshnessGraphView(APIView):
    """Provides graph of actual load and actual acute load of evaluated goal. A goal could be event based or
    could be package based. Evaluation of goal also could be event based or package based"""

    success_msg = "Goal evaluation freshness graph returned successfully."
    error_msg = "Could not retrieve goal freshness graph."

    @swagger_auto_schema(responses=EvaluationFreshnessGraphSchemaView.response)
    @pro_feature
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = user.email + ":v2:" + "goal_evaluation_freshness_graph"

        if cache_key in cache and not force_refresh:
            freshness_graph = cache.get(cache_key)
            logger.info(
                f"Returning goal evaluation freshness graph from cache for user {user.code}"
            )
            response = make_context(False, self.success_msg, freshness_graph)
            return Response(response)

        try:
            logger.info(
                f"Fetching goal evaluation freshness graph for user {user.code}"
            )
            freshness_graph = GoalEvaluationFreshnessGraph(user).get_graph_data()

            cache.set(cache_key, freshness_graph, timeout=settings.CACHE_TIME_OUT)
            response = make_context(False, self.success_msg, freshness_graph)
            return Response(response)
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


class EvaluationGoalTimeInZoneGraphView(APIView):
    """Provides graph of actual load and actual acute load of evaluated goal. A goal could be event based or
    could be package based. Evaluation of goal also could be event based or package based"""

    success_msg = "Goal evaluation time in zone graph returned successfully."
    error_msg = "Could not retrieve goal time in zone graph."

    @swagger_auto_schema(responses=EvaluationTimeInZoneGraphSchemaView.response)
    @pro_feature
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = user.email + ":v2:" + "goal_evaluation_time_in_zone_graph"

        if cache_key in cache and not force_refresh:
            time_in_zone_graph = cache.get(cache_key)
            logger.info(
                f"Returning goal evaluation time in zone graph from cache for user {user.code}"
            )
            response = make_context(False, self.success_msg, time_in_zone_graph)
            return Response(response)

        try:
            logger.info(f"Fetching goal evaluation time in zone for user {user.code}")
            log_extra_args = log_extra_fields(
                user_auth_id=user.id,
                user_id=user.code,
                service_type=ServiceType.API.value,
                request_url=request.path,
            )
            time_in_zone_graph = GoalEvaluationTimeInZoneGraphService(
                user, log_extra_args
            ).get_graph_data()

            cache.set(cache_key, time_in_zone_graph, timeout=settings.CACHE_TIME_OUT)
            response = make_context(False, self.success_msg, time_in_zone_graph)
            return Response(response)
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


class EvaluationGoalTimeVsDistanceGraphView(APIView):
    """Provides graph of actual load and actual acute load of evaluated goal. A goal could be event based or
    could be package based. Evaluation of goal also could be event based or package based"""

    success_msg = "Goal evaluation time vs distance graph returned successfully."
    error_msg = "Could not retrieve goal time vs distance graph."

    @swagger_auto_schema(responses=EvaluationTimeVsDistanceGraphSchemaView.response)
    @pro_feature
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = request.GET.get("force_refresh") == "true"
        cache_key = user.email + ":v2:" + "goal_evaluation_time_vs_distance_graph"

        if cache_key in cache and not force_refresh:
            time_vs_distance_graph = cache.get(cache_key)
            logger.info(
                f"Returning goal evaluation time vs distance graph from cache for user {user.code}"
            )
            response = make_context(False, self.success_msg, time_vs_distance_graph)
            return Response(response)

        try:
            logger.info(
                f"Fetching goal evaluation time vs distance graph for user {user.code}"
            )
            time_vs_distance_graph = GoalEvaluationTimeVsDistanceGraph(
                user
            ).get_graph_data()

            cache.set(
                cache_key, time_vs_distance_graph, timeout=settings.CACHE_TIME_OUT
            )
            response = make_context(False, self.success_msg, time_vs_distance_graph)
            return Response(response)
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
