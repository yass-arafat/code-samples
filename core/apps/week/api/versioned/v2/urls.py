from django.urls import path

from core.apps.week.api.versioned.v2.views import (
    WeekAnalysisFeedbackView,
    WeekAnalysisReportView,
)

urlpatterns = [
    path("analysis", WeekAnalysisReportView.as_view(), name="week-analysis-report"),
    path(
        "analysis/feedback",
        WeekAnalysisFeedbackView.as_view(),
        name="week-analysis-feedback",
    ),
]
