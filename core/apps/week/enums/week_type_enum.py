from enum import Enum


class WeekTypeEnum(Enum):
    BUILD_WEEK = 1
    RECOVERY_WEEK = 2

    @classmethod
    def from_name(cls, name):
        for enum, enum_name in cls.items():
            if enum_name == name:
                return enum
        raise ValueError("{} is not a valid station name".format(name))

    def to_name(self):
        return self[self.value]
