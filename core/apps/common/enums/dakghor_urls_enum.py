from enum import Enum

from django.conf import settings


class DakghorURLEnum(Enum):
    THIRD_PARTY_CONNECT = settings.DAKGHOR_URL + "/api/v1/third-party/connect"
    THIRD_PARTY_DISCONNECT = settings.DAKGHOR_URL + "/api/v1/third-party/disconnect"
    ATHLETE = settings.DAKGHOR_URL + "/api/v1/third-party/athlete"
    ATHLETE_ACTIVITY = settings.DAKGHOR_URL + "/api/v1/private/third-party/activity"
    TIME_IN_ZONE = settings.DAKGHOR_URL + "/api/v1/private/third-party/time-in-zone"

    DATA_MIGRATE = settings.DAKGHOR_URL + "/api/v1/third-party/data-migrate"
    USER_CORE_MIGRATE = settings.DAKGHOR_URL + "/api/v1/third-party/user-code-migrate"
