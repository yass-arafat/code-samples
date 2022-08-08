from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class RecentRideSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User Recent Ride",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Recent ride data returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "activities": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "session_metadata": Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "actual_id": Schema(
                                                    type=openapi.TYPE_INTEGER,
                                                    default=10000,
                                                ),
                                                "session_type": Schema(
                                                    type=openapi.TYPE_STRING,
                                                    default="CYCLING",
                                                ),
                                                "session_label": Schema(
                                                    type=openapi.TYPE_STRING,
                                                    default="Completed Session",
                                                ),
                                            },
                                        ),
                                        "session_date_time": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="2020-12-18T06:00:00Z",
                                        ),
                                        "session_name": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="My Morning Ride",
                                        ),
                                        "session_timespan": Schema(
                                            type=openapi.TYPE_INTEGER, default=7200
                                        ),
                                        "session_distance": Schema(
                                            type=openapi.TYPE_STRING, default="12.5 km"
                                        ),
                                        "session_pss": Schema(
                                            type=openapi.TYPE_INTEGER, default=71
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
                        default="Could not retrieve recent ride data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class HomePageBaseSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Home Page View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Home page view returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "old_home": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "try_a_goal": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "weekly_stats": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "encourage_to_connect": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "encourage_to_record": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "last_activity": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "days_due_of_event": Schema(
                                type=openapi.TYPE_INTEGER, default=0
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
                        default="Could not retrieve home page view",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class TryGoalSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Try a goal event list View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Event list returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "goals": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": Schema(
                                            type=openapi.TYPE_INTEGER, default=""
                                        ),
                                        "name": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                        "image_url": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                        "venue": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                        "event_date": Schema(type=openapi.FORMAT_DATE),
                                        "event_distance": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                        "event_elevation": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                        "description": Schema(
                                            type=openapi.TYPE_STRING, default=""
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
                        default="Could not retrieve Event list",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class WeeklyStatsSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Home Page Weekly Stats View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Home page weekly stats view returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "weekly_distance": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "weekly_duration": Schema(
                                type=openapi.TYPE_INTEGER, default=0
                            ),
                            "weekly_completed_rides": Schema(
                                type=openapi.TYPE_INTEGER, default=0
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
                        default="Could not retrieve weekly stats view",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
