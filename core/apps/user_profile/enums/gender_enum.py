from enum import Enum


class GenderEnum(Enum):
    MALE = ("m", "Male")
    FEMALE = ("f", "Female")
    OTHERS = ("o", "Others")

    @classmethod
    def get_value(cls, member):
        return cls[member].value[0]

    @classmethod
    def get_name(cls, code):
        for x in GenderEnum:
            if x.value[0] == code:
                return x.value[1]
        raise ValueError("{} is not a valid Enum code".format(code))
