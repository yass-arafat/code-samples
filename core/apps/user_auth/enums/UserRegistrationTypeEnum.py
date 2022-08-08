from enum import Enum


class UserRegistrationTypeEnum(Enum):
    EMAIL_SIGNUP = 0
    STRAVA = 1
    GARMIN = 2
    APPLE_HEALTH = 3
    GOOGLE_HEALTH = 4
