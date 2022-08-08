from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class WeekAnalysisReportSchemaView:
    request_schema = Schema(
        title="Week Analysis Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "id": Schema(type=openapi.TYPE_STRING, default=""),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User weekly analysis report View",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="User weekly analysis report returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": Schema(type=openapi.TYPE_STRING, default=""),
                            "is_feedback_saved": Schema(
                                type=openapi.TYPE_BOOLEAN, default=True
                            ),
                            "week_no": Schema(type=openapi.TYPE_INTEGER, default=0),
                            "total_weeks_in_block": Schema(
                                type=openapi.TYPE_INTEGER, default=0
                            ),
                            "week_title": Schema(type=openapi.TYPE_STRING, default=""),
                            "week_start_date": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "week_end_date": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "current_week_remarks": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                    },
                                ),
                            ),
                            "last_week_comparison_remarks": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "tips_for_next_week": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "distance": Schema(type=openapi.TYPE_STRING, default=""),
                            "duration": Schema(type=openapi.TYPE_STRING, default=""),
                            "elevation": Schema(type=openapi.TYPE_STRING, default=""),
                            "total_rides": Schema(type=openapi.TYPE_INTEGER, default=0),
                            "pss": Schema(type=openapi.TYPE_INTEGER, default=0),
                            "is_fthr_available": Schema(
                                type=openapi.TYPE_BOOLEAN, default=True
                            ),
                            "is_ftp_available": Schema(
                                type=openapi.TYPE_BOOLEAN, default=True
                            ),
                            "planned_time_in_power_zones": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                    },
                                ),
                            ),
                            "actual_time_in_power_zones": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                    },
                                ),
                            ),
                            "planned_time_in_hr_zones": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                    },
                                ),
                            ),
                            "actual_time_in_hr_zones": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                        "value": Schema(
                                            type=openapi.TYPE_INTEGER, default=0
                                        ),
                                    },
                                ),
                            ),
                            "feel_feedback": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "week_feedback": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "suggestion_feedback": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "utp_summary": Schema(type=openapi.TYPE_STRING, default=""),
                            "utp_reason": Schema(type=openapi.TYPE_STRING, default=""),
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
                        default="Could not user weekly analysis report detail",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class WeekAnalysisFeedbackSchemaView:
    request_schema = Schema(
        title="Week Analysis Feedback Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "id": Schema(type=openapi.TYPE_STRING, default=""),
            "feel_feedback": Schema(type=openapi.TYPE_STRING, default=""),
            "week_feedback": Schema(type=openapi.TYPE_STRING, default=""),
            "suggestion_feedback": Schema(type=openapi.TYPE_STRING, default=""),
        },
    )

    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Week analysis feedback saved successfully",
            schema=Schema(
                title="Success Response Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Week analysis feedback saved successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Unsuccessful/Error Example",
            schema=Schema(
                title="Could not save week analysis feedback",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not save week analysis feedback",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
