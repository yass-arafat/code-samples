from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class ChallengeOverviewApiV1SchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Challenge Overview",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Challenge overview data returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "available_challenges": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "challenge_metadata": Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "challenge_id": Schema(
                                                    type=openapi.TYPE_INTEGER
                                                )
                                            },
                                        ),
                                        "title": Schema(type=openapi.TYPE_STRING),
                                        "badge_url": Schema(type=openapi.TYPE_STRING),
                                        "description": Schema(type=openapi.TYPE_STRING),
                                        "end_date": Schema(type=openapi.TYPE_STRING),
                                        "background_image_url": Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                        "shareable_link": Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                    },
                                ),
                            ),
                            "current_challenges": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "challenge_metadata": Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "challenge_id": Schema(
                                                    type=openapi.TYPE_INTEGER
                                                )
                                            },
                                        ),
                                        "title": Schema(type=openapi.TYPE_STRING),
                                        "badge_url": Schema(type=openapi.TYPE_STRING),
                                        "description": Schema(type=openapi.TYPE_STRING),
                                        "end_date": Schema(type=openapi.TYPE_STRING),
                                        "background_image_url": Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                        "completion_percentage": Schema(
                                            type=openapi.TYPE_NUMBER
                                        ),
                                        "shareable_link": Schema(
                                            type=openapi.TYPE_STRING
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
                        default="Could not retrieve challenge overview data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class TakeChallengeApiV1SchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "challenge_id": Schema(
                type=openapi.TYPE_INTEGER,
            )
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Challenge Details",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User Challenge description data returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "challenge_metadata": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "challenge_id": Schema(type=openapi.TYPE_INTEGER)
                                },
                            ),
                            "title": Schema(type=openapi.TYPE_STRING),
                            "badge_url": Schema(type=openapi.TYPE_STRING),
                            "description": Schema(type=openapi.TYPE_STRING),
                            "end_date": Schema(type=openapi.TYPE_STRING),
                            "background_image_url": Schema(type=openapi.TYPE_STRING),
                            "shareable_link": Schema(type=openapi.TYPE_STRING),
                            "progress": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "week_no": Schema(type=openapi.TYPE_STRING),
                                        "timeframe": Schema(type=openapi.TYPE_STRING),
                                        "value": Schema(type=openapi.TYPE_STRING),
                                    },
                                ),
                            ),
                            "bottom_sheet_data": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "title": Schema(type=openapi.TYPE_STRING),
                                    "body": Schema(type=openapi.TYPE_STRING),
                                },
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
                        default="Could not retrieve user challenge details data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class ChallengeDescriptionApiV1SchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "challenge_id": Schema(
                type=openapi.TYPE_INTEGER,
            ),
            "challenge_taken": Schema(type=openapi.TYPE_BOOLEAN, default=False),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Challenge Details",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User Challenge description data returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "challenge_metadata": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "challenge_id": Schema(type=openapi.TYPE_INTEGER)
                                },
                            ),
                            "title": Schema(type=openapi.TYPE_STRING),
                            "badge_url": Schema(type=openapi.TYPE_STRING),
                            "description": Schema(type=openapi.TYPE_STRING),
                            "end_date": Schema(type=openapi.TYPE_STRING),
                            "background_image_url": Schema(type=openapi.TYPE_STRING),
                            "shareable_link": Schema(type=openapi.TYPE_STRING),
                            "progress": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "week_no": Schema(type=openapi.TYPE_STRING),
                                        "timeframe": Schema(type=openapi.TYPE_STRING),
                                        "value": Schema(type=openapi.TYPE_STRING),
                                    },
                                ),
                            ),
                            "bottom_sheet_data": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "title": Schema(type=openapi.TYPE_STRING),
                                    "body": Schema(type=openapi.TYPE_STRING),
                                },
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
                        default="Could not retrieve user challenge details data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class AchievedTrophyApiV1SchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Achieved Trophy View",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Achieved trophy badges returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "trophies": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "badge": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="https://pillar-public-bucket.s3.amazonaws.com"
                                            "/challenge/trophy/distance_100km.png",
                                        ),
                                        "name": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="March 100 km Challenge",
                                        ),
                                        "date_time": Schema(
                                            type=openapi.FORMAT_DATETIME,
                                            default="2021-03-17T14:49:00Z",
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_STRING, default="100 km"
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
                        default="Could not retrieve achieved trophy badges",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
