from django.urls import path

from .views import InformationDetailView, InformationSectionView

private_v1_urlpatterns = [
    path(
        "help-and-info/sections",
        InformationSectionView.as_view(),
        name="information-section",
    ),
    path(
        "help-and-info/pages/<int:info_detail_id>",
        InformationDetailView.as_view(),
        name="information-detail",
    ),
]
