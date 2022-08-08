from django.urls import path

from core.apps.settings.api.versioned.v2.views import (
    UserInfoView,
    UserInitSettingsView,
    UserResetSettingsView,
)

urlpatterns = [
    path("init", view=UserInitSettingsView.as_view(), name="user-init-settings"),
    path("reset", view=UserResetSettingsView.as_view(), name="user-settings-reset"),
    path("info", view=UserInfoView.as_view(), name="user-settings-info"),
]
