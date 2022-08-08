from django.urls import path

from . import views

private_v1_urlpatterns = [
    path("connect", views.connect_strava),
    path("disconnect", views.disconnect_strava),
]
