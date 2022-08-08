from enum import Enum

from django.conf import settings


class TreasuryURLEnum(Enum):
    SUBSCRIPTION_CREATE = settings.TREASURY_URL + "/api/v1/subscription/create"
    SUBSCRIPTION_SYNC = settings.TREASURY_URL + "/api/v1/subscription/sync"
