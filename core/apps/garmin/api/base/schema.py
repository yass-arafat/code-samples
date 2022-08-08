from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class SendPillarWorkoutToGarminV1SchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "session_metadata": Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "planned_id": Schema(type=openapi.TYPE_INTEGER, default=1010),
                    "actual_id": Schema(type=openapi.TYPE_INTEGER, default=None),
                    "session_type": Schema(type=openapi.TYPE_STRING, default="CYCLING"),
                    "session_status": Schema(
                        type=openapi.TYPE_STRING, default="PLANNED"
                    ),
                    "session_label": Schema(
                        type=openapi.TYPE_STRING, default="Planned Session"
                    ),
                    "session_label_type": Schema(
                        type=openapi.TYPE_STRING, default="TRAINING_SESSION"
                    ),
                },
            ),
            "workout_name": Schema(type=openapi.TYPE_STRING, default="Workout"),
            "data_type": Schema(type=openapi.TYPE_STRING, default="POWER"),
            "ftp": Schema(type=openapi.TYPE_INTEGER, default=300),
            "fthr": Schema(type=openapi.TYPE_INTEGER, default=None),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Send Workout to Garmin",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Pillar workout sent to Garmin successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "url": Schema(
                                type=openapi.TYPE_STRING,
                                default="https://pillar-public-bucket.s3.eu-west-2.amazonaws.com"
                                "/garmin/workout/SendWorkoutHelperVideo.png",
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Unsuccessful/Error Example",
            schema=Schema(
                title="",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not send Pillar workout to Garmin",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
