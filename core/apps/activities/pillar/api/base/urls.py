from django.urls import path

from .views import ManualActivityView, ThirdPartyActivityView

urlpatterns = [
    path("manual-activity", ManualActivityView.as_view(), name="add-manual-activity"),
    path(
        "third-party-activity",
        ThirdPartyActivityView.as_view(),
        name="third-party-activity",
    ),
]
