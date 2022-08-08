from enum import Enum


class EventTypeEnum(Enum):
    SPORTIVE = (1, "Sportive")
    MULTI_DAY = (2, "Multi Day")
    # TIME_TRIAL = (3, "Time Trial")
    # CRITERIUM = (4, "Criterium")
    # ROAD_RACE = (5, "Road Race")
    # ZWIFT_RACE = (6, "Zwift Race")
    # TRIATHLON = (7, "Triathlon")
    # FITNESS = (8, "Fitness")

    @classmethod
    def get_value(cls, name):
        for x in EventTypeEnum:
            if x.value[1].lower() == name.lower():
                return x.value[0]
        raise ValueError(f"{name} is not a valid Enum name")

    @classmethod
    def get_name(cls, code):
        for x in EventTypeEnum:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError("{} is not a valid Enum code".format(code))

    @classmethod
    def get_capitalized_name(cls, code):
        """
        Return the capitalized name of the enum for the given code to be used in the frontend.
        Remove space, capitalized the name and add "_EVENT" at the end.
        """
        for x in cls:
            if x.value[0] == code:
                return x.value[1].replace(" ", "").upper() + "_EVENT"
        raise ValueError("{} is not a valid Enum code".format(code))

    @classmethod
    def get_code_from_serialized_name(cls, name):
        if not name:
            # return default value
            return cls.SPORTIVE.value[0]

        name = name.replace("_", " ")
        return cls.get_value(name)
