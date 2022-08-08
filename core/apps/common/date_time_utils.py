import datetime
import logging

from .enums.date_time_format_enum import DateTimeFormatEnum

logger = logging.getLogger(__name__)


def convert_str_date_to_date_time_obj(date_str):
    date_time_str = date_str + " 00:00:00.000000"
    try:
        date_time_obj = datetime.datetime.strptime(
            date_time_str, DateTimeFormatEnum.app_date_time_format.value
        )
    except Exception as e:
        logger.error(str(e) + "Couldn't convert date str to date obj")

        date_time_obj = None

    return date_time_obj


def convert_str_date_to_date_obj(date_str):
    try:
        date_obj = datetime.datetime.strptime(
            date_str, DateTimeFormatEnum.app_date_format.value
        ).date()
    except Exception as e:
        logger.error(str(e) + "Couldn't convert date str to date obj")
        date_obj = None

    return date_obj


def convert_str_date_time_to_date_time_obj(date_time_str):
    datetime_format = get_datetime_format(date_time_str)
    try:
        date_time_obj = datetime.datetime.strptime(date_time_str, datetime_format)
    except Exception as e:
        logger.error(str(e) + " Couldn't convert datetime str to datetime obj")
        date_time_obj = None

    return date_time_obj


def convert_str_date_time_zone_to_date_obj(date_time_str):
    try:
        date_time_obj = datetime.datetime.strptime(
            date_time_str, DateTimeFormatEnum.app_date_time_zone_format.value
        )
    except Exception as e:
        logger.error(str(e) + "Couldn't convert date str to date obj")
        date_time_obj = None
    return date_time_obj


def convert_str_time_to_time_obj(time_str):
    try:
        time_obj = datetime.datetime.strptime(
            time_str, DateTimeFormatEnum.app_time_format.value
        )
    except Exception as e:
        logger.error(str(e) + "Couldn't convert date str to date obj")
        time_obj = None

    return time_obj


def convert_timezone_offset_to_seconds(timezone_offset):
    offset_hour, offset_minute = timezone_offset.split(":")
    offset_hour = abs(int(offset_hour))
    offset_minute = int(offset_minute)

    total_seconds = offset_hour * 3600 + offset_minute * 60
    if timezone_offset[0] == "-":
        total_seconds = -total_seconds
    return total_seconds


def time_diff_between_two_timezone_offsets(
    first_timezone_offset, second_timezone_offset
):
    first_offset_second = convert_timezone_offset_to_seconds(first_timezone_offset)
    second_offset_second = convert_timezone_offset_to_seconds(second_timezone_offset)

    return first_offset_second - second_offset_second


class DateTimeUtils:
    @classmethod
    def get_user_local_date_from_utc(cls, timezone_offset, utc_date_time):
        local_date_time = cls.get_user_local_date_time_from_utc(
            timezone_offset, utc_date_time
        )
        return local_date_time.date()

    @classmethod
    def get_user_local_date_time_from_utc(cls, timezone_offset, utc_date_time):

        offset_hour, offset_minute = timezone_offset.split(":")
        offset_hour = int(offset_hour)
        offset_minute = int(offset_minute)

        if offset_hour < 0:
            offset_hour = abs(offset_hour)
            local_date_time = utc_date_time - datetime.timedelta(
                hours=offset_hour, minutes=offset_minute
            )
        else:
            local_date_time = utc_date_time + datetime.timedelta(
                hours=offset_hour, minutes=offset_minute
            )

        return local_date_time

    @classmethod
    def get_utc_date_time_from_local_date_time(cls, timezone_offset, local_date_time):
        offset_hour, offset_minute = timezone_offset.split(":")
        offset_hour = int(offset_hour)
        offset_minute = int(offset_minute)

        if offset_hour < 0:
            offset_hour = abs(offset_hour)
            utc_date_time = local_date_time + datetime.timedelta(
                hours=offset_hour, minutes=offset_minute
            )
        else:
            utc_date_time = local_date_time - datetime.timedelta(
                hours=offset_hour, minutes=offset_minute
            )

        return utc_date_time

    @classmethod
    def get_week_start_datetime_for_user(cls, user, timezone_offset=None):
        # if not timezone_offset:
        #     timezone_offset = user_auth.timezone_offset
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            user.timezone_offset, datetime.datetime.now()
        )
        local_week_start_date = user_local_date - datetime.timedelta(
            days=user_local_date.weekday()
        )
        local_week_start_datetime = datetime.datetime.combine(
            local_week_start_date, datetime.datetime.min.time()
        )
        return local_week_start_datetime

    @classmethod
    def get_week_end_datetime_for_user(cls, user_auth, timezone_offset=None):
        return (
            cls.get_week_start_datetime_for_user(user_auth, timezone_offset)
            + datetime.timedelta(7)
            - datetime.timedelta(seconds=1)
        )

    @staticmethod
    def get_week_start_date(date):
        return date - datetime.timedelta(date.weekday())

    @staticmethod
    def get_week_end_date(date):
        return date + datetime.timedelta(6 - date.weekday())


def add_time_to_datetime_obj(datetime_obj, time_obj):
    hour = time_obj.hour
    minutes = time_obj.minute
    seconds = time_obj.second
    return (
        datetime.timedelta(hours=hour, minutes=minutes, seconds=seconds) + datetime_obj
    )


def get_datetime_format(datetime_str):
    if datetime_str.find("T") != -1 and datetime_str[-1] == "Z":
        return DateTimeFormatEnum.app_default_time_zone_format.value
    elif datetime_str.find("T") != -1:
        return DateTimeFormatEnum.app_default_time_zone_format_alternate.value
    elif datetime_str.find(":") == -1:
        return DateTimeFormatEnum.app_date_format.value
    elif datetime_str[-1] == "Z":
        return (
            DateTimeFormatEnum.app_date_time_zone_format.value
        )  # Depreciated from R12
    return DateTimeFormatEnum.app_date_time_format.value


def daterange(start_date, end_date):
    """Iterates by day over a range of dates"""
    for day_number in range((end_date - start_date).days + 1):
        yield start_date + datetime.timedelta(day_number)


def convert_second_to_str(seconds: int) -> str:
    """Converts seconds to presentable string format (e.g. 10h 10m 10s)"""

    hours = seconds // 3600
    minutes = (seconds - (hours * 3600)) // 60
    seconds -= (minutes * 60) + (hours * 3600)

    output = ""
    if hours:
        output += f"{hours}h"

    if minutes:
        if output:
            output += " "
        output += f"{minutes}m"

    if seconds:
        if output:
            output += " "
        output += f"{seconds}s"

    if not output:
        return "0s"  # 0 second
    return output
