from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class EvaluationGoalSummarySchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Evaluation Summary View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Goal evaluation summary view returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "package_name": Schema(type=openapi.TYPE_STRING),
                            "sub_package_name": Schema(type=openapi.TYPE_STRING),
                            "sub_package_duration": Schema(type=openapi.TYPE_STRING),
                            "package_completion_text": Schema(type=openapi.TYPE_STRING),
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
                        default="Could not retrieve goal evaluation summary data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class EvaluationGoalStatsSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Evaluation Stats View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Goal evaluation stats returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "distance": Schema(type=openapi.TYPE_STRING),
                            "duration": Schema(type=openapi.TYPE_INTEGER),
                            "elevation": Schema(type=openapi.TYPE_STRING),
                            "completed_rides": Schema(type=openapi.TYPE_INTEGER),
                            "pss": Schema(type=openapi.TYPE_INTEGER),
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
                        default="Could not retrieve goal evaluation stats data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class EvaluationGoalScoresSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Evaluation Scores View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Goal evaluation scores returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "total_sessions": Schema(type=openapi.TYPE_INTEGER),
                            "completed_sessions": Schema(type=openapi.TYPE_INTEGER),
                            "session_accuracy_score_average": Schema(
                                type=openapi.TYPE_INTEGER
                            ),
                            "goal_start_load": Schema(type=openapi.TYPE_INTEGER),
                            "goal_end_load": Schema(type=openapi.TYPE_INTEGER),
                            "goal_start_prs": Schema(type=openapi.TYPE_INTEGER),
                            "goal_end_prs": Schema(type=openapi.TYPE_INTEGER),
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
                        default="Could not retrieve goal evaluation scores data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class EvaluationTrainingLoadGraphSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Evaluation Training Load Graph View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Goal evaluation training load graph returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "start_date": Schema(type=openapi.FORMAT_DATE),
                            "end_date": Schema(type=openapi.FORMAT_DATE),
                            "data_points": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "date": Schema(
                                        type=openapi.FORMAT_DATE, default="2021-10-01"
                                    ),
                                    "actual_load": Schema(
                                        type=openapi.TYPE_NUMBER, default=0.0
                                    ),
                                    "actual_acute_load": Schema(
                                        type=openapi.TYPE_NUMBER, default=0.0
                                    ),
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
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=True),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not retrieve goal evaluation training load graph",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class EvaluationFreshnessGraphSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Evaluation Freshness Graph View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Goal evaluation freshness graph returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "start_date": Schema(type=openapi.FORMAT_DATE),
                            "end_date": Schema(type=openapi.FORMAT_DATE),
                            "data_points": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "date": Schema(
                                        type=openapi.FORMAT_DATE, default="2021-10-01"
                                    ),
                                    "freshness_value": Schema(
                                        type=openapi.TYPE_INTEGER, default=0
                                    ),
                                    "freshness_state": Schema(
                                        type=openapi.TYPE_STRING, default="Recovering"
                                    ),
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
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=True),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not retrieve goal evaluation freshness graph",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class EvaluationTimeInZoneGraphSchemaView:
    time_in_zone_list_schema = Schema(
        type=openapi.TYPE_ARRAY,
        items=Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "zone": Schema(type=openapi.TYPE_INTEGER),
                "value": Schema(type=openapi.TYPE_INTEGER),
            },
        ),
    )
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Evaluation Time In Zone Graph View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Goal evaluation time in zone graph returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "data_points": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "date": Schema(
                                        type=openapi.FORMAT_DATE, default="2021-10-01"
                                    ),
                                    "actual_power": time_in_zone_list_schema,
                                    "planned_power": time_in_zone_list_schema,
                                    "actual_heart_rate": time_in_zone_list_schema,
                                    "planned_heart_rate": time_in_zone_list_schema,
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
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=True),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not retrieve goal evaluation time in zone graph",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class EvaluationTimeVsDistanceGraphSchemaView:
    response = {
        status.HTTP_200_OK: openapi.Response(
            description="Goal Evaluation Time Vs Distance Graph View",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Goal evaluation time vs distance graph returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "start_date": Schema(type=openapi.FORMAT_DATE),
                            "end_date": Schema(type=openapi.FORMAT_DATE),
                            "data_points": Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "date": Schema(
                                        type=openapi.FORMAT_DATE, default="2021-10-01"
                                    ),
                                    "actual_duration": Schema(
                                        type=openapi.TYPE_INTEGER, default=0
                                    ),
                                    "distance": Schema(
                                        type=openapi.TYPE_INTEGER, default=0
                                    ),
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
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=True),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not retrieve goal evaluation time vs distance graph",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
