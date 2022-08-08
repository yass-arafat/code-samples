from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class SubscriptionCreateAPISchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Create Subscription",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User subscription created successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT),
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
                        default="Could not retrieve recent ride data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class SubscriptionSyncAPISchemaView:
    request_schema = Schema(
        title="User sync subscription",
        type=openapi.TYPE_OBJECT,
        properties={
            "invoice_code": Schema(type=openapi.TYPE_STRING, default=""),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Subscription Sync",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User subscription created successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT),
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
                        default="Could not retrieve recent ride data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
