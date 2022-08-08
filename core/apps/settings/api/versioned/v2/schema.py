from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class UserInitSettingsSchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "email": Schema(type=openapi.TYPE_STRING),
            "code": Schema(type=openapi.TYPE_STRING),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User initial settings",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User initial settings saved successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
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
                        default="Could not save user's initial settings",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserResetSettingsSchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "fcm_device_token": Schema(type=openapi.TYPE_STRING),
            "code": Schema(type=openapi.TYPE_STRING),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User reset settings",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User settings reset successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
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
                        default="Could not reset user's initial settings",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserInfoSchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "code": Schema(type=openapi.TYPE_STRING),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User reset settings",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User info returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        default=None,
                        properties={
                            "access_level": Schema(type=openapi.TYPE_STRING),
                            "is_garmin_connected": Schema(type=openapi.TYPE_BOOLEAN),
                            "is_strava_connected": Schema(type=openapi.TYPE_BOOLEAN),
                            "is_wahoo_connected": Schema(type=openapi.TYPE_BOOLEAN),
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
                        default="Could not return user info",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
