import enum


class SecondBySecondDataEnum(enum.Enum):
    POWER = (0, "power")
    POWER_ZONE = (1, "power_zone")
    HEART_RATE = (2, "heart_rate")
    HEART_RATE_ZONE = (3, "heart_rate_zone")
    SPEED = (4, "speed")
    CADENCE = (5, "cadence")
    DISTANCE = (6, "distance")
    ELEVATION = (7, "elevation")
    TEMPERATURE = (8, "temperature")
    TIME = (9, "time")
    LATITUDE = (10, "latitude")
    LONGITUDE = (11, "longitude")
    LEFT_LEG_POWER = (12, "left_leg_power")
    RIGHT_LEG_POWER = (13, "right_leg_power")
    POWER_250 = (14, "power_250")
    POWER_250_TIME = (15, "power_250_time")
    POWER_250_ZONE = (16, "power_250_zone")
    HEART_RATE_250 = (17, "heart_rate_250")
    HEART_RATE_250_TIME = (18, "heart_rate_250_time")
    HEART_RATE_250_ZONE = (19, "heart_rate_250_zone")
