from core.apps.activities.pillar.utils import get_average_speed_from_ride_summary
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.services import RoundServices

from .dictionary import get_session_info_dict_v2


def get_activity_info_v2(actual_session, athlete_activity, user_personalise_data):
    is_uploaded_activity = bool(
        actual_session.third_party.code != ThirdPartySources.MANUAL.value[0]
    )

    if athlete_activity is None and is_uploaded_activity:
        calories_burnt = (
            weighted_power
        ) = (
            pss
        ) = (
            intensity
        ) = average_speed = elapsed_time = moving_time = distance = elevation = None

    elif is_uploaded_activity:
        pss = round(actual_session.actual_pss)
        intensity = int(actual_session.actual_intensity * 100)

        average_speed = get_average_speed_from_ride_summary(
            athlete_activity["ride_summary"]
        )

        weighted_power = None
        if athlete_activity["weighted_power"] and user_personalise_data.current_ftp:
            weighted_power = round(athlete_activity["weighted_power"])

        elapsed_time = athlete_activity["elapsed_time"]
        moving_time = athlete_activity["moving_time"]
        calories_burnt = RoundServices.round_calories_burnt(
            athlete_activity["calories_burnt"]
        )
        distance = RoundServices.round_distance(
            actual_session.actual_distance_in_meters / 1000
        )
        elevation = RoundServices.round_elevation(actual_session.elevation_gain)
    else:
        pillar_data = actual_session.pillar_data
        moving_time = pillar_data.moving_time_in_seconds
        elapsed_time = pillar_data.moving_time_in_seconds
        distance = round(pillar_data.total_distance_in_meter / 1000, 1)
        average_speed = round(pillar_data.average_speed, 1)
        elevation = None
        pss = round(actual_session.actual_pss)
        intensity = int(actual_session.actual_intensity * 100)
        weighted_power = None
        calories_burnt = None

    return get_session_info_dict_v2(
        moving_time,
        elapsed_time,
        distance,
        average_speed,
        elevation,
        intensity,
        pss,
        weighted_power,
        calories_burnt,
    )
