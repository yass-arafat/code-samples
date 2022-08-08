from enum import Enum


class DistanceTypeEnum(Enum):
    SHORT = (1, "Short")
    MEDIUM = (2, "Medium")
    LONG = (3, "Long")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]

    @classmethod
    def get_name(cls, code):
        for x in DistanceTypeEnum:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError("{} is not a valid Enum code".format(code))
