from enum import Enum


class DateTimeFormatEnum(Enum):
    app_date_time_format = "%Y-%m-%d %H:%M:%S.%f"
    app_date_time_zone_format = "%Y-%m-%d %H:%M:%S.%fZ"
    app_default_time_zone_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    app_default_time_zone_format_alternate = "%Y-%m-%dT%H:%M:%S.%f"
    app_date_format = "%Y-%m-%d"
    app_time_format = "%H:%M:%S"
    date_time_format = "%Y-%m-%d %H:%M:%S"
