from django.urls import path

from . import views

urlpatterns = [
    # /notifications
    path("", views.NotificationView.as_view()),
    path("new", views.NewNotificationView.as_view()),
    # /notifications/
    path("user", views.UserNotificationView.as_view()),
    path("user/<int:notification_id>/actions", views.UserNotificationView.as_view()),
    path("list", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "ack/<int:push_notification_id>",
        views.PushNotificationAcknowledgeView.as_view(),
    ),
    # Push Notification from other microservices
    path("push-notifications", views.PushNotificationView.as_view()),
    # /sync/
    path("update", views.SyncUpdateView.as_view()),
]

private_v1_urlpatterns = [
    path("device-token", views.DeviceTokenView.as_view()),
    # in app notification
    path(
        "in-app",
        views.InAppNotificationView.as_view(),
        name="in-app-notification",
    ),
    path(
        "panel",
        views.NotificationPanelView.as_view(),
        name="notification-panel",
    ),
    path(
        "in-app/deactivate",
        views.DeactivateInAppNotificationView.as_view(),
        name="in-app-notification",
    ),
    path("sync-init", views.SyncView.as_view()),
]

# TODO Remove it when every user moves to > R16.2
private_v1_sync_urlpatterns = [
    path("init", views.SyncView.as_view()),
]
