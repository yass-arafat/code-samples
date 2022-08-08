from enum import Enum


class ThirdPartySources(Enum):
    GARMIN = (1, "Garmin")
    STRAVA = (2, "Strava")
    WAHOO = (3, "Wahoo")
    MANUAL = (4, "Manual")

    @classmethod
    def choices(cls):
        return [key.value for key in cls]

    @classmethod
    def get_code_from_text(cls, text):
        for x in cls:
            if x.value[1].lower() == text:
                return x.value[0]
        raise ValueError("{} is not a valid Enum text".format(text))
