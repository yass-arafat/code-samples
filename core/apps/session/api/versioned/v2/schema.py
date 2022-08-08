from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class SessionFeedbackSchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "session_metadata": Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "actual_id": Schema(type=openapi.TYPE_INTEGER, default=1),
                    "planned_id": Schema(type=openapi.TYPE_INTEGER, default=1),
                    "session_type": Schema(type=openapi.TYPE_STRING, default="cycling"),
                    "session_status": Schema(
                        type=openapi.TYPE_STRING, default="PAIRED"
                    ),
                    "is_manual_activity": Schema(
                        type=openapi.TYPE_BOOLEAN, default=True
                    ),
                    "session_label_type": Schema(
                        type=openapi.TYPE_STRING, default="TRAINING_SESSION"
                    ),
                },
            ),
            "effort_level": Schema(type=openapi.TYPE_INTEGER, default=7),
            "session_followed_as_planned": Schema(
                type=openapi.TYPE_BOOLEAN, default=False
            ),
            "reason": Schema(type=openapi.TYPE_STRING, default="reason"),
            "explanation": Schema(type=openapi.TYPE_STRING, default="Lorem Ipsum"),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Session Feedback",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Session feedback saved successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "actual_id": Schema(type=openapi.TYPE_INTEGER, default=1),
                            "planned_id": Schema(type=openapi.TYPE_INTEGER, default=1),
                            "session_type": Schema(
                                type=openapi.TYPE_STRING, default="cycling"
                            ),
                            "session_status": Schema(
                                type=openapi.TYPE_STRING, default="PAIRED"
                            ),
                            "is_manual_activity": Schema(
                                type=openapi.TYPE_BOOLEAN, default=True
                            ),
                            "session_label_type": Schema(
                                type=openapi.TYPE_STRING, default="TRAINING_SESSION"
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not save session feedback",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
