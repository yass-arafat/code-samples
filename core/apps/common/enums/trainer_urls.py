from enum import Enum

from django.conf import settings


class TrainerURLEnum(Enum):
    DATA_MIGRATE = settings.TRAINER_URL + "/api/v1/common/data-migrate"
    CALCULATE_MORNING_DATA = settings.TRAINER_URL + "/api/v1/day/calculate-morning-data"
    MIGRATE_DATA = settings.TRAINER_URL + "/api/v1/migrate/data"
    MIGRATE_USER_PLAN = settings.TRAINER_URL + "/private/api/v1/migrate/user-plan"
    MIGRATE_TRAINING_AVAILABILITY = (
        settings.TRAINER_URL + "/private/api/v1/migrate/training-availability"
    )
    MIGRATE_PLANNED_SESSION = (
        settings.TRAINER_URL + "/private/api/v1/migrate/planned-session"
    )
    MIGRATE_USER_KNOWLEDGE_HUB = (
        settings.TRAINER_URL + "/private/api/v1/migrate/user-knowledge-hub"
    )
    MIGRATE_PERSONAL_RECORD = (
        settings.TRAINER_URL + "/private/api/v1/migrate/personal-record"
    )
    MIGRATE_USER_AWAY = settings.TRAINER_URL + "/private/api/v1/migrate/user-away"
    MIGRATE_CHALLENGE = settings.TRAINER_URL + "/private/api/v1/migrate/challenge"
    MIGRATE_USER_CHALLENGE = (
        settings.TRAINER_URL + "/private/api/v1/migrate/user-challenge"
    )
    MIGRATE_PLANNED_DAY = settings.TRAINER_URL + "/private/api/v1/migrate/planned-day"
    MIGRATE_USER_BLOCK = settings.TRAINER_URL + "/private/api/v1/migrate/user-block"
    MIGRATE_USER_WEEK = settings.TRAINER_URL + "/private/api/v1/migrate/user-week"
    MIGRATE_PILLAR_DATA = settings.TRAINER_URL + "/private/api/v1/migrate/pillar-data"
    MIGRATE_ACTUAL_DAY_DATA = (
        settings.TRAINER_URL + "/private/api/v1/migrate/actual-day"
    )
    MIGRATE_CURVE_CALCULATION_DATA = (
        settings.TRAINER_URL + "/private/api/v1/migrate/curve-calculation"
    )
    MIGRATE_ATHLETE_STATE_DATA = (
        settings.TRAINER_URL + "/private/api/v1/migrate/athlete-state"
    )
    MIGRATE_ATHLETE_DIFFICULTY_STATE_DATA = (
        settings.TRAINER_URL + "/private/api/v1/migrate/athlete-difficulty-state"
    )
    MIGRATE_USER_MESSAGE = settings.TRAINER_URL + "/private/api/v1/migrate/user-message"
    RUN_UTP = settings.TRAINER_URL + "/private/api/v1/week/portal/update-user-weeks"
    FIX_BROKEN_WEEK = settings.TRAINER_URL + "/private/api/v1/week/fix-broken-weeks"
    CLEAR_CACHE = settings.TRAINER_URL + "/api/v1/user/clear-cache"
