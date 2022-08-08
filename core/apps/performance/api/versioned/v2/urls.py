from django.urls import path

from . import views

urlpatterns = [
    path("overview", views.PerformanceOverviewViewV2.as_view()),
    path("stats/overview", views.PerformanceStatsViewV2.as_view()),
    path("prs/overview", views.PrsOverviewViewV2.as_view()),
    path("freshness/overview", views.FreshnessOverviewViewV2.as_view()),
    path("training-load/overview", views.TrainingLoadOverviewViewV2.as_view()),
    path("threshold/overview", views.ThresholdOverviewViewV2.as_view()),
    path("time-in-zone/overview", views.TimeInZoneOverviewViewV2.as_view()),
    path(
        "zone-difficulty-level/overview",
        views.ZoneDifficultyLevelOverviewViewV2.as_view(),
    ),
    path("stats/graph/year/<int:year>", views.StatsGraphApiView.as_view()),
    path("prs/graph/year/<int:year>", views.PrsGraphApiView.as_view()),
    path("freshness/graph/year/<int:year>", views.FreshnessGraphApiView.as_view()),
    path("training-load/graph/year/<int:year>", views.LoadGraphApiView.as_view()),
    path("threshold/graph", views.ThresholdGraphApiView.as_view()),
    path("time-in-zone/graph/year/<int:year>", views.TimeInZoneGraphApiView.as_view()),
]
