from enum import Enum


class SessionStatusEnum(str, Enum):
    PLANNED = "PLANNED"
    UNPAIRED = "UNPAIRED"
    PAIRED = "PAIRED"

    @classmethod
    def lower(cls):
        lower = {s.lower() for s in cls.__members__}
        return lower


class SessionTypeEnum(str, Enum):
    RECOVERY = "RECOVERY"
    CYCLING = "CYCLING"
    RUNNING = "RUNNING"
    SWIMMING = "SWIMMING"
    I_AM_AWAY = "I_AM_AWAY"

    @classmethod
    def lower(cls):
        lower = {s.lower() for s in cls.__members__}
        return lower


class SessionLabelTypeEnum(str, Enum):
    COMMUTE = "COMMUTE"
    TRAINING_SESSION = "TRAINING_SESSION"
    EVENT = "EVENT"
    MULTIDAY_EVENT = "MULTIDAY_EVENT"

    @classmethod
    def lower(cls):
        lower = {label.lower() for label in cls.__members__}
        return lower


class SessionLabelEnum(str, Enum):
    COMPLETED_SESSION = "Completed Session"
    EVALUATED_SESSION = "Evaluated Session"
    PLANNED_SESSION = "Planned Session"
    COMPLETED_COMMUTE = "Completed Commute"
    EVALUATED_COMMUTE = "Evaluated Commute"
    PLANNED_COMMUTE = "Planned Commute"
    COMPLETED_EVENT = "Completed Event"
    EVALUATED_EVENT = "Evaluated Event"
    PLANNED_EVENT = "Planned Event"
    MULTIDAY_EVENT = "Multi Day Event"
    I_AM_AWAY = "I am away"

    @classmethod
    def lower(cls):
        lower = {label.lower() for label in cls.__members__}
        return lower


class SessionNameEnum(str, Enum):
    AWAY_SESSION_NAME = "I am away"
