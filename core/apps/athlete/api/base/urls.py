from django.urls import path

from .views import (
    AthleteCalendarApiView,
    AthleteDailyPrsGraphApiView,
    AthleteFileProcessInfo,
    AthleteFileProcessInfoList,
    AthleteInfoApiView,
    AthleteLoadGraphApiView,
    AthleteOverviewApiView,
    AthleteRecoveryGraphApiView,
    AthleteSpecificDateBaselineFitness,
    AthleteSqsGraphApiView,
    AthleteTodayFocusAPIView,
    CoachInfoApiView,
    SessionDetailsApiView,
)

urlpatterns = [
    path("<int:id>", AthleteInfoApiView.as_view()),
    path("<int:id>/overview", AthleteOverviewApiView.as_view()),
    path("<int:user_id>/today-focus", AthleteTodayFocusAPIView.as_view()),
    path(
        "<int:user_id>/plan/year/<str:year>/month/<str:month>",
        AthleteCalendarApiView.as_view(),
    ),
    path(
        "<int:user_id>/evaluation/daily/get-daily-prs",
        AthleteDailyPrsGraphApiView.as_view(),
    ),
    path(
        "<int:user_id>/evaluation/daily/get-load-graph",
        AthleteLoadGraphApiView.as_view(),
    ),
    path(
        "<int:user_id>/evaluation/daily/get-seven-days-recovery-graph",
        AthleteRecoveryGraphApiView.as_view(),
    ),
    path(
        "<int:user_id>/evaluation/daily/get-seven-days-sqs-graph",
        AthleteSqsGraphApiView.as_view(),
    ),
    path(
        "<int:user_id>/session/get-session-details/<int:session_id>",
        SessionDetailsApiView.as_view(),
    ),
    path("<int:id>/coach/info", CoachInfoApiView.as_view()),
    path(
        "<int:user_id>/profile/baseline-fitness",
        AthleteSpecificDateBaselineFitness.as_view(),
    ),
    path("<int:user_id>/profile/file-process-info", AthleteFileProcessInfo.as_view()),
    path(
        "<int:user_id>/profile/file-process-info-list",
        AthleteFileProcessInfoList.as_view(),
    ),
]
