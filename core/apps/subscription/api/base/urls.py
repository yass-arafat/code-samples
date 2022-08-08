from django.urls import path

from core.apps.subscription.api.base.views import (
    SubscriptionCreateAPIView,
    SubscriptionSyncAPIView,
)

urlpatterns = [
    path("create", SubscriptionCreateAPIView.as_view(), name="subscription-create"),
    path("sync", SubscriptionSyncAPIView.as_view(), name="subscription-sync"),
]
