from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class WahooConnectViewSchema:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "access_token": Schema(type=openapi.TYPE_STRING, default=""),
            "expires_in": Schema(type=openapi.TYPE_INTEGER, default=7199),
            "refresh_token": Schema(type=openapi.TYPE_STRING, default=""),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Wahoo connected successful",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Wahoo connected failed",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class WahooDisconnectViewSchema:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Wahoo disconnected successful",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Wahoo disconnected failed",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
