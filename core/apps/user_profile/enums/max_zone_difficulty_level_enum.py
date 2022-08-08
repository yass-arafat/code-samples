import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MaxZoneDifficultyLevel(Enum):
    # zone number, max level
    ZONE_3 = (3, 5)  # Level 0-5
    ZONE_4 = (4, 6)  # Level 0-6
    ZONE_5 = (5, 5)  # Level 0-5
    ZONE_6 = (6, 5)  # Level 0-5
    ZONE_7 = (7, 5)  # Level 0-5
    ZONE_HC = ("HC", 2)  # Level 0-2

    @classmethod
    def get_max_level(cls, zone_no):
        for zone_level in cls:
            if zone_level.value[0] == zone_no:
                return zone_level.value[1]
        raise ValueError(
            f"Zone: {zone_no} do not have any defined max difficulty level"
        )
