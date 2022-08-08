from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class UserOnboardingViewSchema:
    tags = ["user profile"]
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "name": Schema(type=openapi.TYPE_STRING, default="John Doe"),
            "gender": Schema(type=openapi.TYPE_STRING, default="Male"),
            "date_of_birth": Schema(type=openapi.TYPE_STRING, default="1996-02-20"),
            "weight": Schema(type=openapi.TYPE_NUMBER, default=72.0),
            "ftp": Schema(type=openapi.TYPE_INTEGER, default=300),
            "fthr": Schema(type=openapi.TYPE_INTEGER, default=160),
            "max_heart_rate:": Schema(type=openapi.TYPE_INTEGER, default=180),
            "timezone_offset": Schema(type=openapi.TYPE_STRING, default="6:00"),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Saved user onboarding data successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not save onboarding data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class CreateTrainingPlanV2SchemaView:
    request_schema = Schema(
        title="Request Data Example",
        type=openapi.TYPE_OBJECT,
        properties={
            "event_data": Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id": Schema(type=openapi.TYPE_INTEGER, default=1),
                    "event_date": Schema(
                        type=openapi.FORMAT_DATETIME, default="2022-08-14 00:00:00.000"
                    ),
                    "event_name": Schema(
                        type=openapi.TYPE_STRING, default="Ride London 100"
                    ),
                    "event_type": Schema(type=openapi.TYPE_STRING, default=None),
                    "elevation_gain": Schema(type=openapi.TYPE_NUMBER, default=1903.00),
                    "event_sub_type": Schema(type=openapi.TYPE_STRING, default=None),
                    "distance_per_day": Schema(
                        type=openapi.TYPE_NUMBER, default=100.00
                    ),
                    "performance_goal": Schema(
                        type=openapi.TYPE_STRING, default="Podium"
                    ),
                },
            ),
            "schedule_data": Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "days_commute_by_bike": Schema(
                        type=openapi.TYPE_ARRAY,
                        items=Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    ),
                    "commute_to_work_by_bike": Schema(
                        type=openapi.TYPE_BOOLEAN, default=False
                    ),
                    "duration_single_commute": Schema(
                        type=openapi.TYPE_NUMBER, default=0.0
                    ),
                    "available_training_hours_per_day_outside_commuting": Schema(
                        type=openapi.TYPE_ARRAY,
                        items=Schema(type=openapi.TYPE_NUMBER, default=6.0),
                    ),
                },
            ),
            "training_hours_over_last_4_weeks": Schema(
                type=openapi.TYPE_NUMBER, default=5.0
            ),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Saved goal data and created training plan successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING, default="Could not save goal data"
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserBasicInfoV2ViewSchema:
    tags = ["user profile"]
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned User Basic Info Successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not return User Basic Info",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserFitnessInfoV2ViewSchema:
    tags = ["user profile"]
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned User Fitness Data Successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not return User Fitness Data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserFitnessInfoExistV2ViewSchema:
    tags = ["user profile"]
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "activity_datetime": Schema(type=openapi.TYPE_STRING),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned User fitness exist info Successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not return User fitness data exist info",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserFileProcessInfoV2ViewSchema:
    tags = ["user profile"]
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "activity_datetime": Schema(type=openapi.TYPE_STRING),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned User file process info Successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not return User file process info",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserAvailabilityDataV2ViewSchema:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned User availability Data Successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not return User availability Data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserTimezoneDataViewV2Schema:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned User availability Data Successfully",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not return User availability Data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class UserSupportSchemaView:
    tags = ["user profile"]
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "name": Schema(type=openapi.TYPE_STRING, default="John Doe"),
            "email": Schema(type=openapi.TYPE_STRING, default="john.doe@gmail.com"),
            "type_of_issue": Schema(type=openapi.TYPE_STRING, default="File Upload"),
            "date_of_issue": Schema(type=openapi.TYPE_STRING, default="2020-01-01"),
            "message": Schema(type=openapi.TYPE_STRING, default="File Upload Issue"),
            "app_version": Schema(type=openapi.TYPE_STRING, default="1.0.0"),
            "device_model": Schema(type=openapi.TYPE_STRING, default="iPhone"),
            "file": Schema(type=openapi.TYPE_FILE, default=None),
            "user_log": Schema(type=openapi.TYPE_FILE, default=None),
        },
    )
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(type=openapi.TYPE_STRING, default=""),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
            description="Response data example",
            schema=Schema(
                title="Unsuccessful/Error Example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(type=openapi.TYPE_STRING, default=""),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
