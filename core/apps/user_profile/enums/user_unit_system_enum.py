from enum import Enum


class UserUnitSystemEnum(Enum):
    METRIC = ("M", "Metric")
    IMPERIAL = ("I", "Imperial")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]

    @classmethod
    def get_name(cls, code):
        for x in UserUnitSystemEnum:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError("{} is not a valid Enum code".format(code))
