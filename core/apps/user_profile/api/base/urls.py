from django.urls import path

from . import views

v1_urlpatterns = [
    path("", views.UserInfoView.as_view()),
    path("profile/settings", views.UserSettingsView.as_view()),  # deprecated in R15
    path("profile/settings/info", views.UserProfileView.as_view()),
    path("profile/settings/timezone", views.TimeZoneView.as_view()),
    path("profile/settings/notification", views.PushNotificationSettingsView.as_view()),
    path("training/availability", views.UserTrainingAvailabilityView.as_view()),
    path("create/training-plan/", views.CreateTrainingPlan.as_view()),
    # path("personalise-data", views.UserPersonaliseDataApiView.as_view()),
    path("add-new-goal", views.AddNewGoalApiView.as_view()),
    path("coach-athletes-info", views.AthletesInfoApiView.as_view()),
    path(
        "activity-logs", views.UserActivityLogsApiView.as_view(), name="activity-logs"
    ),
    path("subscription", views.SubscriptionAPIView.as_view(), name="subscription-test"),
    path("payment-sync", views.PaymentSyncAPIView.as_view(), name="payment-sync"),
    # Internal APIs
    path("timezone", views.UserTimeZoneView.as_view(), name="user-timezone"),
    path(
        "timezone/user-ids", views.TimeZoneUserView.as_view(), name="timezone-user-ids"
    ),
    path(
        "starting-values",
        views.UserStartingValuesView.as_view(),
        name="user-starting-values",
    ),
    path(
        "history-input-date",
        views.UserFirstHistoryInputDateView.as_view(),
        name="first-history-input-date",
    ),
    path("baseline-fitness", views.UserBaselineFitnessView.as_view()),
    path(
        "baseline-fitness-daterange", views.UserBaselineFitnessDateRangeView.as_view()
    ),
    path("current-baseline-fitness", views.UserCurrentBaselineFitnessView.as_view()),
    path("personalise-data", views.UserPersonaliseDataApiView.as_view()),
    path("personalise-data-list", views.UserPersonaliseDataListApiView.as_view()),
    path("current-personalise-data", views.UserCurrentPersonaliseDataApiView.as_view()),
    path("clear-cache", views.ClearUserCacheView.as_view(), name="clear-cache"),
]

private_v1_urlpatterns = [
    path("profile/picture", views.UserProfilePictureView.as_view()),
    path("metadata", views.UserMetadataApiView.as_view()),
    # TODO refactor this api path with more specific context
    # this api is invoked only when user don't have any ftp or fthr given
    # but trying to access power or hr related session details. so instead
    # of the path name baseline fitness request, change this a better context name
    path(
        "profile/baseline-fitness-request",
        views.UserBaselineFitnessRequestView.as_view(),
    ),
]
