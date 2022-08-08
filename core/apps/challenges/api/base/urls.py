from django.urls import path

from .views import (
    AchievedTrophyApiV1,
    ChallengeDescriptionApiV1,
    ChallengeOverviewApiV1,
    TakeChallengeApiV1,
)

urlpatterns = [
    path("overview", ChallengeOverviewApiV1.as_view(), name="challenge-overview"),
    path(
        "description", ChallengeDescriptionApiV1.as_view(), name="challenge-description"
    ),
    path("take", TakeChallengeApiV1.as_view(), name="challenge-take"),
    path("trophy", AchievedTrophyApiV1.as_view(), name="challenge-trophy"),
]
