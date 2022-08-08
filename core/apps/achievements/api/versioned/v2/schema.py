from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class AchievementOverviewSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Achievement Overview",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Achievement overview data returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "achievements": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "badge": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="https://pillar-public-bucket.s3.eu-west-2.amazonaws.com"
                                            "/achievement/badge/LongestRide.png",
                                        ),
                                    },
                                ),
                            )
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
                        default="Could not retrieve achievement overview data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class PersonalRecordSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Personal Record View",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Personal record summary returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "achievements": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "badge": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="https://pillar-public-bucket.s3.eu-west-2.amazonaws.com"
                                            "/achievement/badge/LongestRide.png",
                                        ),
                                        "name": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="Longest Ride",
                                        ),
                                        "date_time": Schema(
                                            type=openapi.FORMAT_DATETIME,
                                            default="2021-02-07T14:49:00Z",
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="2.50 Hr/s",
                                        ),
                                        "level": Schema(
                                            type=openapi.TYPE_INTEGER, default=8
                                        ),
                                        "history": Schema(
                                            type=openapi.TYPE_OBJECT, default=None
                                        ),
                                        "achievement_metadata": Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "is_active": Schema(
                                                    type=openapi.TYPE_BOOLEAN,
                                                    default=True,
                                                ),
                                                "record_type": Schema(
                                                    type=openapi.TYPE_INTEGER, default=2
                                                ),
                                            },
                                        ),
                                    },
                                ),
                            )
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
                        default="Could not retrieve personal record summary",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class RecordDetailSchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "is_active": Schema(type=openapi.TYPE_BOOLEAN, default=True),
            "record_type": Schema(type=openapi.TYPE_INTEGER, default=2),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Record Detail View",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Personal record detail returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "badge": Schema(
                                type=openapi.TYPE_STRING,
                                default="https://pillar-public-bucket.s3.eu-west-2.amazonaws.com"
                                "/achievement/badge/LongestRide.png",
                            ),
                            "name": Schema(
                                type=openapi.TYPE_STRING, default="Longest Ride"
                            ),
                            "date_time": Schema(
                                type=openapi.FORMAT_DATETIME,
                                default="2021-02-07T14:49:00Z",
                            ),
                            "value": Schema(
                                type=openapi.TYPE_STRING, default="2.50 Hr/s"
                            ),
                            "level": Schema(type=openapi.TYPE_INTEGER, default=8),
                            "history": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "level": Schema(
                                            type=openapi.TYPE_INTEGER, default=6
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="1.50 Hr/s",
                                        ),
                                        "date_time": Schema(
                                            type=openapi.FORMAT_DATETIME,
                                            default="2021-02-06T14:29:00Z",
                                        ),
                                    },
                                ),
                            ),
                            "achievement_metadata": Schema(
                                type=openapi.TYPE_OBJECT, default=None
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
                        default="Could not retrieve personal record detail",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
