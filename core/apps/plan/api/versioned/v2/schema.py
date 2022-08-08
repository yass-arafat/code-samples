from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class PlanStatsV2SchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Plan Stats View",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Plan Stats Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "event_name": Schema(
                                type=openapi.TYPE_STRING, default="Ride London 100"
                            ),
                            "sports_type": Schema(
                                type=openapi.TYPE_STRING, default="CYCLING"
                            ),
                            "sessions_completed": Schema(
                                type=openapi.TYPE_INTEGER, default=20
                            ),
                            "sessions_remaining": Schema(
                                type=openapi.TYPE_INTEGER, default=30
                            ),
                            "days_till_event": Schema(
                                type=openapi.TYPE_INTEGER, default=38
                            ),
                            "has_goal": Schema(type=openapi.TYPE_BOOLEAN, default=True),
                            "event_date": Schema(
                                type=openapi.FORMAT_DATE, default="2021-12-12"
                            ),
                            "performance_goal": Schema(
                                type=openapi.TYPE_STRING, default="complete"
                            ),
                            "goal_progress_percentage": Schema(
                                type=openapi.TYPE_NUMBER, default=0.62
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
                        default="Failed to fetch plan stats data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class GoalDetailSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Details View",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned goal details successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "event_name": Schema(
                                type=openapi.TYPE_STRING, default="Ride London 100"
                            ),
                            "sports_type": Schema(
                                type=openapi.TYPE_STRING, default="CYCLING"
                            ),
                            "sessions_completed": Schema(
                                type=openapi.TYPE_INTEGER, default=20
                            ),
                            "sessions_remaining": Schema(
                                type=openapi.TYPE_INTEGER, default=30
                            ),
                            "days_till_event": Schema(
                                type=openapi.TYPE_INTEGER, default=38
                            ),
                            "event_date": Schema(
                                type=openapi.FORMAT_DATE, default="2021-12-12"
                            ),
                            "performance_goal": Schema(
                                type=openapi.TYPE_STRING, default="complete"
                            ),
                            "goal_progress_percentage": Schema(
                                type=openapi.TYPE_NUMBER, default=0.62
                            ),
                            "event_elevation": Schema(
                                type=openapi.TYPE_INTEGER, default="400 m"
                            ),
                            "event_distance": Schema(
                                type=openapi.TYPE_INTEGER, default="140 km Ride"
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
                        type=openapi.TYPE_STRING, default="Failed to fetch goal details"
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class DeleteGoalSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Delete Goal",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Deleted current goal successfully",
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
                        default="Failed to delete current goal",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
