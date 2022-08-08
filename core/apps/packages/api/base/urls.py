from django.urls import path

from . import views

urlpatterns = [
    path("", views.PackageListView.as_view(), name="package-list"),
    path("<int:package_id>", views.PackageInfoView.as_view(), name="package-info"),
    path(
        "<int:package_id>/sub-packages",
        views.SubPackageView.as_view(),
        name="sub-packages",
    ),
    path(
        "<int:package_id>/sub-packages/<int:sub_package_id>/durations",
        views.PackageDurationView.as_view(),
        name="package-duration",
    ),
    path(
        "<int:package_id>/knowledge-hub",
        views.PackageKnowledgeHubView.as_view(),
        name="base-knowledge-hub",
    ),
    path(
        "knowledge-hub/<int:knowledge_hub_id>",
        views.KnowledgeHubView.as_view(),
        name="base-knowledge-hub",
    ),
]
