from django.urls import path

from . import views

urlpatterns = [
    path("overview", views.PlanOverviewViewV2.as_view()),
    path("stats", views.PlanStatsViewV2.as_view()),
    path("delete", views.DeleteGoalView.as_view(), name="delete-goal"),
    path("details", views.GoalDetailView.as_view(), name="goal-details"),
]
