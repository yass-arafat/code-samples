from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class BaselineFitnessApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Baseline Fitness Data",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned user baseline fitness data successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "current_ftp": Schema(
                                type=openapi.TYPE_INTEGER, default=310
                            ),
                            "current_threshold_heart_rate": Schema(
                                type=openapi.TYPE_INTEGER, default=170
                            ),
                            "max_heart_rate": Schema(
                                type=openapi.TYPE_INTEGER, default=190
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="",
            schema=Schema(
                title="Un-success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User baseline fitness data not found",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class PushNotificationSettingsApiSchemaView:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={"is_push_notification_enabled": Schema(type=openapi.TYPE_BOOLEAN)},
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data examples",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Saved push notification settings successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        )
    }
    get_api_responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data examples",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned push notification settings successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "is_push_notification_enabled": Schema(
                                type=openapi.TYPE_BOOLEAN, default=True
                            )
                        },
                    ),
                },
            ),
        )
    }


class UserMetadataApiSchemaView:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "build_number": Schema(
                type=openapi.TYPE_STRING, description="application version"
            ),
            "device_info": Schema(
                type=openapi.TYPE_OBJECT,
                description="User device information",
                properties={"device_model": Schema(type=openapi.TYPE_STRING)},
            ),
            "hash_value": Schema(
                type=openapi.TYPE_STRING,
                description="User metadata hash value,"
                " it will be null if there is no value",
            ),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Athlete basic info for coach",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="false"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Athlete info returned successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="",
            schema=Schema(
                title="Un-success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING, default="Did not match secret key"
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserActivityLogsApiSchemaView:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "dakghor_api_secret_key": Schema(
                type=openapi.TYPE_STRING, description="API Secret Key for Dakghor"
            ),
            "activity_logs": Schema(
                type=openapi.TYPE_ARRAY,
                items=Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "request": Schema(type=openapi.TYPE_OBJECT),
                        "response": Schema(type=openapi.TYPE_OBJECT),
                        "user_auth_id": Schema(type=openapi.TYPE_INTEGER),
                        "data": Schema(type=openapi.TYPE_OBJECT),
                        "activity_code": Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response of Activity Logs from Dakghor",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Activity logs received successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        )
    }


class CreateTrainingPlanSchemaView:
    request_schema = Schema(
        title="Request data example", type=openapi.TYPE_OBJECT, properties={}
    )
