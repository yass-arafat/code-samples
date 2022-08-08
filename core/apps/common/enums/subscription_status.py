import enum


class SubscriptionStatusEnum(enum.Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    TRIAL = "TRIAL"

    @classmethod
    def lower(cls):
        lower = {status.lower() for status in cls.__members__}
        return lower
