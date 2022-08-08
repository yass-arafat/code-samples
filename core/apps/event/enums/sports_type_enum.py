from enum import Enum


class SportsTypeEnum(Enum):
    CYCLING = "CYCLING"

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)
