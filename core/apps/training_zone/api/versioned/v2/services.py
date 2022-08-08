from datetime import datetime

from core.apps.common.dictionary.training_zone_dictionary import (
    training_zone_truth_table_dict as training_zones,
)
from core.apps.common.utils import (
    get_heart_rate_upper_boundary,
    get_power_upper_boundary,
)
from core.apps.user_profile.utils import get_user_fthr, get_user_ftp

from .dictionary import get_training_zone_dictionary, get_zone_boundary_dictionary


class TrainingZonesServices:
    @staticmethod
    def get_power_zone_boundaries(current_ftp):
        if not current_ftp:
            return []

        power_zone_boundaries = []
        for idx in training_zones:
            zone_no = training_zones[idx]["zone_focus"]
            zone_name = training_zones[idx]["zone_name"]

            lower_bound = round(
                (training_zones[idx]["power_ftp_lower_bound"] / 100) * current_ftp
            )
            upper_bound = round(
                (training_zones[idx]["power_ftp_upper_bound"] / 100) * current_ftp
            )
            if zone_no == 7:
                upper_bound = get_power_upper_boundary(current_ftp)
            zone_boundary_text = f"{lower_bound} Watts to {upper_bound} Watts"

            power_zone_boundaries.append(
                get_zone_boundary_dictionary(zone_no, zone_name, zone_boundary_text)
            )

        return power_zone_boundaries

    @staticmethod
    def get_heart_rate_zone_boundaries(current_fthr):
        if not current_fthr:
            return []

        heart_rate_zone_boundaries = []
        for idx in training_zones:
            zone_no = training_zones[idx]["zone_focus"]

            zone_name = training_zones[idx]["zone_name"]

            lower_bound = round(
                (training_zones[idx]["heart_rate_fthr_lower_bound"] / 100)
                * current_fthr
            )
            upper_bound = round(
                (training_zones[idx]["heart_rate_fthr_upper_bound"] / 100)
                * current_fthr
            )
            if zone_no == 6:
                upper_bound = get_heart_rate_upper_boundary(current_fthr)
            zone_boundary_text = f"{lower_bound} bpm to {upper_bound} bpm"
            if zone_no == 7:
                zone_boundary_text = ""
            heart_rate_zone_boundaries.append(
                get_zone_boundary_dictionary(zone_no, zone_name, zone_boundary_text)
            )

        return heart_rate_zone_boundaries

    @classmethod
    def get_training_zones(cls, user_auth):
        current_datetime = datetime.now()
        current_ftp = get_user_ftp(user_auth, current_datetime)
        current_fthr = get_user_fthr(user_auth, current_datetime)

        power_zone_boundaries = cls.get_power_zone_boundaries(current_ftp)
        heart_rate_zone_boundaries = cls.get_heart_rate_zone_boundaries(current_fthr)

        return get_training_zone_dictionary(
            current_ftp, current_fthr, power_zone_boundaries, heart_rate_zone_boundaries
        )
