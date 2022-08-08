from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class FreshnessOverviewV2ApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Freshness overview for user",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Freshness Overview Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "freshness_value": Schema(
                                type=openapi.TYPE_INTEGER,
                                description="User current freshness",
                                default=0,
                            ),
                            "freshness_title": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "freshness_remarks": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="",
            schema=Schema(
                title="Failed to fetch freshness overview data",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch freshness overview data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class TrainingLoadOverviewV2ApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Training load overview for user",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Training Load Overview Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "load_title": Schema(type=openapi.TYPE_STRING, default=""),
                            "load_remarks": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                        },
                    ),
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="",
            schema=Schema(
                title="Failed to fetch training load overview data",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch training load overview data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class ThresholdOverviewV2ApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Threshold overview for user",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Threshold Overview Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "current_ftp": Schema(
                                type=openapi.TYPE_INTEGER, default=None
                            ),
                            "current_fthr": Schema(
                                type=openapi.TYPE_INTEGER, default=None
                            ),
                            "threshold_remarks": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                        },
                    ),
                },
            ),
        )
    }


class TimeInZoneOverviewV2ApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Time in Zone overview for user",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Time in Zone Overview Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "time_in_zone_remarks": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "time_in_zones": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "zone_no": Schema(
                                            type=openapi.TYPE_INTEGER, default=""
                                        ),
                                        "zone_name": Schema(
                                            type=openapi.TYPE_STRING, default=""
                                        ),
                                        "time_spent_in_zone": Schema(
                                            type=openapi.TYPE_INTEGER, default=""
                                        ),
                                        "completion_percentage": Schema(
                                            type=openapi.TYPE_INTEGER, default=""
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
                title="Failed to fetch Time in Zone Overview data",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=True),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch Time in Zone Overview data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class ZoneDifficultyLevelOverviewV2ApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Zone Difficulty Level overview for user",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Zone Difficulty Level Overview Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "difficulty_level_remarks": Schema(
                                type=openapi.TYPE_STRING, default=""
                            ),
                            "difficulty_levels": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "level_name": Schema(
                                            type=openapi.TYPE_STRING, default="Zone 3"
                                        ),
                                        "current_level": Schema(
                                            type=openapi.TYPE_INTEGER, default=2
                                        ),
                                        "max_level": Schema(
                                            type=openapi.TYPE_INTEGER, default=6
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
                title="Failed to fetch Zone Difficulty Level Overview data",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=True),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch Zone Difficulty Level Overview data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class LoadGraphApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User performance load graph",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Load Graph Data Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "has_previous_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "has_next_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "year": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "date": Schema(
                                            type=openapi.FORMAT_DATE, default=""
                                        ),
                                        "chronic_load": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
                                        ),
                                        "acute_load": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
                                        ),
                                        "actual_chronic_load": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
                                        ),
                                        "actual_acute_load": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
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
                title="Failed to fetch load graph data",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch load graph data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class ThresholdGraphApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User performance threshold graph",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Threshold Graph Data Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "has_previous_data": Schema(type=openapi.TYPE_BOOLEAN),
                            "has_next_data": Schema(type=openapi.TYPE_BOOLEAN),
                            "is_power_data_available": Schema(
                                type=openapi.TYPE_BOOLEAN
                            ),
                            "is_hr_data_available": Schema(type=openapi.TYPE_BOOLEAN),
                            "is_weight_available": Schema(type=openapi.TYPE_BOOLEAN),
                            "graph_data": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "timeframe": Schema(type=openapi.TYPE_INTEGER),
                                        "power": Schema(type=openapi.TYPE_INTEGER),
                                        "power_date": Schema(type=openapi.FORMAT_DATE),
                                        "power_per_weight": Schema(
                                            type=openapi.TYPE_INTEGER
                                        ),
                                        "power_per_weight_date": Schema(
                                            type=openapi.FORMAT_DATE
                                        ),
                                        "heart_rate": Schema(type=openapi.TYPE_INTEGER),
                                        "heart_rate_date": Schema(
                                            type=openapi.FORMAT_DATE
                                        ),
                                    },
                                ),
                            ),
                        },
                    ),
                },
            ),
        )
    }


class StatsGraphApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User performance stats graph",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Stats Graph Data Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "has_previous_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "has_next_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "year": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "date": Schema(
                                            type=openapi.FORMAT_DATE, default=""
                                        ),
                                        "distance": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
                                        ),
                                        "planned_duration": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
                                        ),
                                        "actual_duration": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
                                        ),
                                        "elevation": Schema(
                                            type=openapi.FORMAT_DOUBLE, default=""
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
                title="Failed to fetch stats graph data",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch stats graph data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class PrsGraphApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User performance prs graph",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned PRS Graph Data Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "has_previous_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "has_next_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "year": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "date": Schema(
                                            type=openapi.FORMAT_DATE,
                                            default="2021-10-01",
                                        ),
                                        "actual_prs": Schema(
                                            type=openapi.TYPE_INTEGER, default="29"
                                        ),
                                        "planned_prs": Schema(
                                            type=openapi.TYPE_INTEGER, default="54"
                                        ),
                                        "sas_today": Schema(
                                            type=openapi.TYPE_INTEGER, default="31"
                                        ),
                                        "session_score": Schema(
                                            type=openapi.TYPE_INTEGER, default="72"
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
                title="PRS Graph retrieval failed",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not fetch PRS graph data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class FreshnessGraphApiSchemaView:
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User performance freshness graph",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="False"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Freshness Graph Data Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "has_previous_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "has_next_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "year": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "date": Schema(
                                            type=openapi.FORMAT_DATE,
                                            default="2021-10-01",
                                        ),
                                        "freshness_value": Schema(
                                            type=openapi.TYPE_INTEGER, default="0"
                                        ),
                                        "freshness_state": Schema(
                                            type=openapi.TYPE_STRING,
                                            default="Recovering",
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
                title="Freshness Graph retrieval failed",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Could not fetch freshness graph data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }


class TimeInZoneGraphApiSchemaView:
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
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="User performance time in zone graph",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Returned Time In Zone Graph Data Successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "has_previous_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="True"
                            ),
                            "has_next_data": Schema(
                                type=openapi.TYPE_BOOLEAN, default="False"
                            ),
                            "year": Schema(
                                type=openapi.TYPE_ARRAY,
                                items=Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "date": Schema(type=openapi.FORMAT_DATE),
                                        "actual_power": time_in_zone_list_schema,
                                        "planned_power": time_in_zone_list_schema,
                                        "actual_heart_rate": time_in_zone_list_schema,
                                        "planned_heart_rate": time_in_zone_list_schema,
                                        "actual_combined": time_in_zone_list_schema,
                                        "planned_combined": time_in_zone_list_schema,
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
                title="Failed to fetch time in zone graph data",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_BOOLEAN, default="True"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Failed to fetch time in zone graph data",
                    ),
                    "data": Schema(type=openapi.TYPE_OBJECT, default=None),
                },
            ),
        ),
    }
