from django.urls import path

from .views import SendPillarWorkoutToGarminV1, garmin_connect, garmin_disconnect

private_v1_urlpatterns = [
    path("connect", garmin_connect),
    path("disconnect", garmin_disconnect),
    path(
        "workout/send",
        SendPillarWorkoutToGarminV1.as_view(),
        name="send_workout_to_garmin",
    ),
]
