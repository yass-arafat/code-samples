from enum import Enum


class SessionTypeEnum(Enum):
    interval = (1, "Intervals")
    easy = (2, "Easy")
    long = (3, "Long")
    high_intensity_maintenence = (4, "High Intensity Maintenence")
    event = (5, "Event")
    recovery_day = (6, "Recovery Day")
    commute = (7, "Commute")

    @classmethod
    def get_name(cls, code):
        for x in SessionTypeEnum:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError("{} is not a valid Enum code".format(code))
