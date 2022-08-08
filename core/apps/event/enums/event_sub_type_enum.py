from enum import Enum
from math import inf


class EventSubTypeEnum(Enum):
    FLAT = (1, "Flat")
    HILLY = (2, "Hilly")
    MOUNTAIN = (3, "Mountain")
    # TEN_MILES = (4, 'Ten Miles')
    # TWENTY_FIVE_MILES = (5, '25 miles')
    # FIFTY_PLUS_MILES = (6, '50+ plus')
    # SHORT = (7, 'Short')
    # LONG = (8, 'Long')
    # FLAT_OR_ROLLING = (9, 'Flat or Rolling')
    # OLYMPIC = (10, 'Olympic')
    # HALF_IRONMAN = (11, 'Half Ironman')
    # IRONMAN = (12, 'Ironman')

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]

    @classmethod
    def get_name(cls, code):
        for x in EventSubTypeEnum:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError("{} is not a valid Enum code".format(code))

    @classmethod
    def get_value_from_name(cls, name):
        for x in EventSubTypeEnum:
            if x.value[1] == name:
                return x.value[0]
        raise ValueError("{} is not a valid Enum name".format(name))


class ClimbingRatioEnum(Enum):
    FLAT = (0, 10)
    HILLY = (11, 22)
    MOUNTAIN = (23, inf)
