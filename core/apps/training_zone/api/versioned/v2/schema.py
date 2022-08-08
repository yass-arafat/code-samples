from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class TrainingZonesViewV2ApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Use Training Zones",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Training Zones Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "current_fthr": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="User current FTHR",
                                default=310,
                            ),
                            "current_ftp": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="User current FTP",
                                default=170,
                            ),
                            "power_zone_boundaries": Schema(
                                type=openapi.TYPE_ARRAY,
                                description="User Power Zone Boundaries",
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone_number": Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Zone No",
                                        ),
                                        "zone_name": Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Zone Name",
                                        ),
                                        "zone_boundary": Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Lower and Upper Boundary of Zone",
                                        ),
                                    },
                                ),
                            ),
                            "heart_rate_zone_boundaries": Schema(
                                type=openapi.TYPE_ARRAY,
                                description="User Heart Rate Zone Boundaries",
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone_number": Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Zone No",
                                        ),
                                        "zone_name": Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Zone Name",
                                        ),
                                        "zone_boundary": Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Lower and Upper Boundary of Zone",
                                        ),
                                    },
                                ),
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="",
            schema=Schema(
                title="Training Zones Not Found",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch training zones data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
