from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class PackageDurationSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Package Dration List Overview",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Package duration returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "caption": Schema(type=openapi.TYPE_STRING, default=""),
                            "duration_list": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "duration": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                        "description": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                    },
                                ),
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
                        default="Package duration returned failed",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
