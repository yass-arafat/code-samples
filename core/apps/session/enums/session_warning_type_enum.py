from enum import Enum


class SessionWarningTypeEnum(str, Enum):
    PSS = "PSS"
    FRESHNESS = "FRESHNESS"
    INTENSITY = "INTENSITY"

    @classmethod
    def lower(cls):
        lower = {s.lower() for s in cls.__members__}
        return lower
