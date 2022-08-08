from django.urls import path

from core.apps.data_provider.wahoo.api.versioned.v2.views import (
    WahooConnectView,
    WahooDisconnectView,
)

private_v2_urlpatterns = [
    path("connect", WahooConnectView.as_view(), name="wahoo-connect"),
    path("disconnect", WahooDisconnectView.as_view(), name="wahoo-disconnect"),
]
