from django.urls import path

from .views import (
    CreateTrainingPlanViewV2,
    UserBasicInfoViewV2,
    UserFileProcessInfoViewV2,
    UserFitnessInfoExistViewV2,
    UserFitnessInfoViewV2,
    UserOnboardingView,
    UserPortalOnboardingView,
    UserProfileInfoViewV2,
    UserSupportView,
    UserTimezoneDataViewV2,
)

url_patterns = [
    path("create/training-plan", CreateTrainingPlanViewV2.as_view()),
]

url_patterns_private_v2 = [
    path(
        "fitness-info-exist",
        UserFitnessInfoExistViewV2.as_view(),
        name="user-fitness-info-exist",
    ),
    path(
        "file-process-info",
        UserFileProcessInfoViewV2.as_view(),
        name="file-process-info",
    ),
    path("onboard", UserOnboardingView.as_view(), name="user-onboarding"),
    path(
        "portal/onboard",
        UserPortalOnboardingView.as_view(),
        name="user-portal-onboarding",
    ),
    path("basic-info", UserBasicInfoViewV2.as_view(), name="user-basic-info"),
    path("fitness-info", UserFitnessInfoViewV2.as_view(), name="user-fitness-info"),
    path("timezone-info", UserTimezoneDataViewV2.as_view(), name="user-timezone-info"),
    path("support", UserSupportView.as_view(), name="user-support"),
    path(
        "info", UserProfileInfoViewV2.as_view()
    ),  # this api is for common tabs in FE, where image and name is needed everytime
]
