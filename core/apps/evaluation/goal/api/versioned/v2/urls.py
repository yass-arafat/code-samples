from django.urls import path

from . import views

urlpatterns = [
    path(
        "summary",
        views.EvaluationGoalSummaryView.as_view(),
        name="goal-evaluation-summary",
    ),
    path(
        "stats", views.EvaluationGoalStatsView.as_view(), name="goal-evaluation-stats"
    ),
    path(
        "scores",
        views.EvaluationGoalScoresView.as_view(),
        name="goal-evaluation-scores",
    ),
    path(
        "training-load/graph",
        views.EvaluationGoalTrainingLoadGraphView.as_view(),
        name="goal-evaluation-training-load-graph",
    ),
    path(
        "freshness/graph",
        views.EvaluationGoalFreshnessGraphView.as_view(),
        name="freshness-graph",
    ),
    path(
        "time-in-zone/graph",
        views.EvaluationGoalTimeInZoneGraphView.as_view(),
        name="time-in-zone-graph",
    ),
    path(
        "time-vs-distance/graph",
        views.EvaluationGoalTimeVsDistanceGraphView.as_view(),
        name="time-vs-distance-graph",
    ),
]
