from enum import Enum


class ServiceType(Enum):
    INTERNAL = "internal"
    API = "api"
    CRON = "cron"
    ADMIN = "admin"
    THIRD_PARTY = "third_party"
