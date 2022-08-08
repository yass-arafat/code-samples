from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class AthleteInfoApiSchemaView:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "coach_api_secret_key": Schema(
                type=openapi.TYPE_STRING,
                description="coach api secret key",
                default="CEmeMC8Q3vUnOaUSsdfRes858kU&@3Wdsiru88JXKVXEEwrp9mQzsnmmpxvViMVsbmGvwwcOFHdJz",
            ),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Athlete basic info for coach",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="false"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Athlete info returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": Schema(
                                type=openapi.TYPE_STRING, description="athlete id"
                            ),
                            "profile_picture_url": Schema(
                                type=openapi.TYPE_STRING,
                                description="s3 url of athletes profile picture",
                            ),
                            "full_name": Schema(
                                type=openapi.TYPE_STRING,
                                description="athletes full name",
                            ),
                            "age": Schema(
                                type=openapi.TYPE_INTEGER, description="athletes age"
                            ),
                            "zone_focus_name": Schema(
                                type=openapi.TYPE_STRING,
                                description="athletes today zone focus name",
                            ),
                            "starting_prs": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="athletes starting prs when he started the plan",
                            ),
                            "current_prs": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="athletes today prs",
                            ),
                            "target_prs": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="athletes target prs",
                            ),
                            "rides_completed": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="no of rides that is completed in current active plan",
                            ),
                            "total_distance": Schema(
                                type=openapi.TYPE_NUMBER,
                                description="distance that needs to be covered in current active plan",
                            ),
                            "days_due_of_event": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="no of days left in event",
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="",
            schema=Schema(
                title="Un-success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING, default="Did not match secret key"
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class AthleteOverviewApiSchemaView:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "coach_api_secret_key": Schema(
                type=openapi.TYPE_STRING,
                description="coach api secret key",
                default="CEmeMC8Q3vUnOaUSsdfRes858kU&@3Wdsiru88JXKVXEEwrp9mQzsnmmpxvViMVsbmGvwwcOFHdJz",
            ),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Athlete upcoming and past rides info for coach",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="false"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Athlete info returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "upcoming_rides": Schema(
                                type=openapi.TYPE_OBJECT,
                                description="Upcoming rides of athlete",
                                properties={
                                    "id": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="planned session id",
                                    ),
                                    "date": Schema(
                                        type=openapi.TYPE_STRING,
                                        description="planned session date",
                                    ),
                                    "session_name": Schema(
                                        type=openapi.TYPE_STRING,
                                        description="planned session name",
                                    ),
                                    "session_type_name": Schema(
                                        type=openapi.TYPE_STRING,
                                        description="planned session type name",
                                    ),
                                    "zone_focus": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="planned session zone focus",
                                    ),
                                    "planned_duration": Schema(
                                        type=openapi.TYPE_NUMBER,
                                        description="planned session duration",
                                    ),
                                    # Depreciated from R7
                                    "session_timespan": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="planned session duration in seconds, depreciated from R7",
                                    ),
                                    # For backwards compatibility, delete when no one is using R3 anymore
                                    "session_type": Schema(
                                        type=openapi.TYPE_STRING,
                                        description="planned session type name, depreciated from R3",
                                    ),
                                    "planned_session_duration": Schema(
                                        type=openapi.TYPE_NUMBER,
                                        description="planned session duration, depreciated from R3",
                                    ),
                                },
                            ),
                            "past_rides": Schema(
                                type=openapi.TYPE_OBJECT,
                                description="s3 url of athletes profile picture",
                                properties={
                                    "id": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="past session id",
                                    ),
                                    "date": Schema(
                                        type=openapi.TYPE_STRING,
                                        description="past session date",
                                    ),
                                    "session_name": Schema(
                                        type=openapi.TYPE_STRING,
                                        description="past session name",
                                    ),
                                    "session_type_name": Schema(
                                        type=openapi.TYPE_STRING,
                                        description="past session type name",
                                    ),
                                    "zone_focus": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="past session zone focus",
                                    ),
                                    "is_completed": Schema(
                                        type=openapi.TYPE_BOOLEAN,
                                        description="Session completed or not",
                                    ),
                                    "is_evaluation_done": Schema(
                                        type=openapi.TYPE_BOOLEAN,
                                        description="Session evaluated or not",
                                    ),
                                    "session_timespan": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="planned session duration in seconds,"
                                        " depreciated from R7",
                                    ),
                                    "overall_accuracy_score": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="overall accuracy score",
                                    ),
                                    "prs_accuracy_score": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="prs accuracy score",
                                    ),
                                    # Depreciated from R8
                                    "overall_score": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="overall score, depreciated from R8",
                                    ),
                                    "prs_score": Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="prs score, depreciated from R8",
                                    ),
                                    # Depreciated from R7
                                    "planned_duration": Schema(
                                        type=openapi.TYPE_NUMBER,
                                        description="planned session duration",
                                    ),
                                    "actual_duration": Schema(
                                        type=openapi.TYPE_NUMBER,
                                        description="actual session duration",
                                    ),
                                },
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="",
            schema=Schema(
                title="Un-success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING, default="Did not match secret key"
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
