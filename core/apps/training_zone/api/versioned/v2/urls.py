from django.urls import path

from . import views

urlpatterns = [
    path("", views.TrainingZonesViewV2.as_view()),
]
