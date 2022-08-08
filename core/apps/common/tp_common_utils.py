import logging
from datetime import datetime

from core.apps.activities.enums import SecondBySecondDataEnum
from core.apps.settings.models import ThirdPartySettings

from ..activities.utils import dakghor_get_athlete_info
from .const import CURVE_CALCULATION_WINDOWS
from .dictionary.tp_dictionary import get_cadence_dict, get_hr_dict, get_power_dict
from .utils import get_duplicate_session_timerange

logger = logging.getLogger(__name__)


class AliasDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.aliases = {}

    def __getitem__(self, key):
        return dict.__getitem__(self, self.aliases.get(key, key))

    def __setitem__(self, key, value):
        return dict.__setitem__(self, self.aliases.get(key, key), value)

    def add_alias(self, key, alias):
        self.aliases[alias] = key

    def add_aliases(self, aliases: list):
        for key, alias in aliases:
            self.add_alias(key, alias)


def get_third_party_instance(third_party_code):
    third_party = ThirdPartySettings.objects.filter(
        code=third_party_code, is_active=True
    ).first()
    return third_party


def get_max_average(cumulative_ride_data, curve_window):
    ride_data_len = len(cumulative_ride_data)

    if curve_window > ride_data_len:
        return None

    start_index = 0
    end_index = curve_window - 1
    max_ride = -1
    while end_index < ride_data_len:
        ride_sum = cumulative_ride_data[end_index]
        if start_index:
            ride_sum -= cumulative_ride_data[start_index - 1]

        max_ride = max(max_ride, round(ride_sum / curve_window))

        start_index += 1
        end_index += 1
    return max_ride if max_ride != -1 else None


def calculate_curve(ride_data):
    if not ride_data:
        return []

    cumulative_data = []
    for ride in ride_data:
        if cumulative_data:
            cumulative_data.append(cumulative_data[-1] + ride["value"])
        else:
            cumulative_data.append(ride["value"])

    max_averages = [
        get_max_average(cumulative_data, curve_window)
        for curve_window in CURVE_CALCULATION_WINDOWS
    ]

    return list(filter(None, max_averages))


def same_session_date_time_exists(activity_start_time: datetime, user, tp_source_code):
    """
    Checks if any session of this user with same session date time (+/- TIME_RANGE_BOUNDARY seconds) as the current
    activity already exists.
    """
    start_time, end_time = get_duplicate_session_timerange(activity_start_time)
    return user.actual_sessions.filter(
        session_date_time__range=(start_time, end_time),
        third_party__code=tp_source_code,
        is_active=True,
    ).exists()


def read_s3_pillar_power_data(worksheet):
    power_column = SecondBySecondDataEnum.POWER.value[0] + 1
    power_zone_column = SecondBySecondDataEnum.POWER_ZONE.value[0] + 1

    power_data = []
    for x in range(2, worksheet.max_row + 1):
        power_value = worksheet.cell(row=x, column=power_column).value
        power_zone_value = worksheet.cell(row=x, column=power_zone_column).value
        if power_value is None:
            break
        power_data.append(get_power_dict(power_value, power_zone_value))

    logger.info(f"Total power data: {len(power_data)}")
    return power_data


def read_s3_pillar_heart_rate_data(worksheet):
    heart_rate_column = SecondBySecondDataEnum.HEART_RATE.value[0] + 1
    heart_rate_zone_column = SecondBySecondDataEnum.HEART_RATE_ZONE.value[0] + 1

    heart_rate_data = []
    for x in range(2, worksheet.max_row + 1):
        heart_rate_value = worksheet.cell(row=x, column=heart_rate_column).value
        heart_rate_zone_value = worksheet.cell(
            row=x, column=heart_rate_zone_column
        ).value
        if heart_rate_value is None:
            break
        heart_rate_data.append(get_hr_dict(heart_rate_value, heart_rate_zone_value))

    logger.info(f"Total heart rate data: {len(heart_rate_data)}")
    return heart_rate_data


def read_s3_pillar_cadence_data(worksheet):
    cadence_column = SecondBySecondDataEnum.CADENCE.value[0] + 1

    cadence_data = []
    for x in range(2, worksheet.max_row + 1):
        cadence_value = worksheet.cell(row=x, column=cadence_column).value
        if cadence_value is None:
            break
        cadence_data.append(get_cadence_dict(cadence_value))

    logger.info(f"Total cadence data: {len(cadence_data)}")
    return cadence_data


def read_s3_pillar_compressed_data(worksheet, value_column, time_column, zone_column):
    data_list = []
    for x in range(2, worksheet.max_row + 1):
        value = worksheet.cell(row=x, column=value_column).value
        if value is None:
            break
        data_list.append(
            {
                "value": value,
                "time": worksheet.cell(row=x, column=time_column).value,
                "zone_focus": worksheet.cell(row=x, column=zone_column).value,
            }
        )
    return data_list


def read_s3_pillar_compressed_power_data(worksheet):
    power_column = SecondBySecondDataEnum.POWER_250.value[0] + 1
    time_column = SecondBySecondDataEnum.POWER_250_TIME.value[0] + 1
    zone_column = SecondBySecondDataEnum.POWER_250_ZONE.value[0] + 1
    return read_s3_pillar_compressed_data(
        worksheet, power_column, time_column, zone_column
    )


def read_s3_pillar_compressed_hr_data(worksheet):
    hr_column = SecondBySecondDataEnum.HEART_RATE_250.value[0] + 1
    time_column = SecondBySecondDataEnum.HEART_RATE_250_TIME.value[0] + 1
    zone_column = SecondBySecondDataEnum.HEART_RATE_250_ZONE.value[0] + 1
    return read_s3_pillar_compressed_data(
        worksheet, hr_column, time_column, zone_column
    )


def is_third_party_connected(user_code):
    user_info = dakghor_get_athlete_info(user_code)
    return (
        True
        if user_info["is_garmin_connected"]
        or user_info["is_strava_connected"]
        or user_info["is_wahoo_connected"]
        else False
    )
