from django.urls import path

from .views import HomePageBaseView, RecentRideView, TryGoalView, WeeklyStatsView

urlpatterns = [
    path("", HomePageBaseView.as_view(), name="base-home"),
    path("activities", RecentRideView.as_view(), name="recent-ride"),
    path(
        "goals", TryGoalView.as_view(), name="home-page-try-goals"
    ),  # deprecated in R13
    path("stats", WeeklyStatsView.as_view(), name="home-page-weekly-stats"),
]
