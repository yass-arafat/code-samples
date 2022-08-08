from django.urls import path

from . import views

private_v1_urlpatterns = [
    path("data", views.MigrateDataView.as_view()),
]
