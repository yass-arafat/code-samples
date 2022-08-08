import os
from datetime import time

PSS_SL_MIN = 24
MIN_WEEKLY_PSS = 105

POWER_UPPER_BOUNDARY_COEFFICIENT = 8
HEART_RATE_UPPER_BOUNDARY_COEFFICIENT = 1.25

CHRONIC_LOAD_BUFFER = 3.5
LOAD_OVERTRAINING_LIMIT = 8.0

ALLOWABLE_PERCENTAGE = 0.25

PRS_BUFFER = 1

STARTING_SQS = 5
STARTING_SAS = 50
MIN_STARTING_LOAD = 15
MIN_AVAILABLE_TRAINING_HOUR = 0.75
MAX_TYPICAL_INTENSITY = 0.73

MAX_ACTIVITY_HOURS_OF_ACTIVITY_FILE = 24
MAX_ACTIVITY_FILE_SIZE = 5242880

FIRST_TIMEZ0NE_OFFSET = "+13:00"

MIDNIGHT_CRONJOB_TIME = time(23, 55, 0, 0)
MORNING_CRONJOB_TIME = time(23, 55, 0, 0)
WEEK_ANALYSIS_CRONJOB_TIME = time(0, 20, 0, 0)
LOAD_SQS_CHANGE_CHECK_CRONJOB_TIME = time(3, 0, 0, 0)

LOAD_CHANGE_LIMIT = 3
SQS_CHANGE_LIMIT = 2.5
IMPORTANT_TIMEZONES = (11, 12, 21, 22)

TODAYS_NOTIFICATION_CRONJOB_TIME = time(0, 1, 0, 0)

MANUAL_EDIT_BACK_TO_BACK_HIGH_INTENSITY = 0.80
DEFAULT_EXPIRE_TIME = "23:59:59.0000"

NOTIFICATION_EXPIRE_TIME = 24

ACCESS_TOKEN_TIMEOUT = 2592000.0  # 1 month
REFRESH_TOKEN_TIMEOUT = 7776000.0  # 3 months

ACCESS_TOKEN_ADVANCE_REFRESH_TIME = 10.0  # 10 seconds

MTP_OVER_TRAINING_INTENSITY = 0.80

# units of speed, heart rate, power and elevation gain are km/h, bpm, watts and meter respectively
THIRD_PARTY_DIFFERENCE_THRESHOLD_VALUES = {
    "avg_speed": 1,
    "max_speed": 2,
    "avg_heart_rate": 2,
    "max_heart_rate": 2,
    "avg_power": 5,
    "max_power": 5,
    "elevation_gain": 75,
}
FTP_BOUNDARY = {"lowest": 30, "highest": 500}
FTHR_BOUNDARY = {"lowest": 80, "highest": 200}
MAX_HR_BOUNDARY = {"lowest": 100, "highest": 230}
MAX_HR_TO_FTHR_COEFFICIENT = 0.7

MAX_AVERAGE_SPEED = 99.9  # km/h
MAX_SESSION_DURATION = 86399  # seconds
MAX_SESSION_DISTANCE = 999900  # meters
AVERAGE_HEART_RATE_BOUNDARY = {"lowest": 40, "highest": 230}
AVERAGE_POWER_BOUNDARY = {"lowest": 1, "highest": 1000}

# For converting m/s to km/hr
METER_PER_SECOND_TO_KM_PER_HOUR = 3.6

TRAFFIC_LIGHT_THRESHOLD_VALUE = 15

USER_UTP_SETTINGS_QUEUE_PRIORITIES = [0, 1, 2, 3, 4, 5]

CURVE_CALCULATION_WINDOWS = [
    5,
    10,
    20,
    30,
    60,
    120,
    300,
    600,
    1200,
    2400,
    3600,
    5400,
    7200,
    9000,
    10800,
]

TIME_RANGE_BOUNDARY = 60  # seconds

GARMIN_ACTIVITY_FILE_EXTENTION = ".fit"
STRAVA_ACTIVITY_FILE_EXTENTION = ".pb"
PILLAR_DATA_FILE_EXTENSION = ".xlsx"

MAX_SINGLE_RIDE_MULTIPLIER = 3.6
MINIMUM_FRESHNESS = -20
MAX_REPEATED_INTENSITY = 0.73

PERSONAL_RECORD_DURATION_CHECK_UNIT = "minutes"

TEMPORARY_ACTIVITY_FILES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "activity_files"
)

NO_CURRENT_GOAL = "No Current Goal"
BACKFILL_REQUEST_DAY_LIMIT = 90

NOTIFICATIONS_PER_PAGE = 10
HIGHEST_NOTIFICATION_SHOW = (
    "9+"  # It is shown when not shown notifications are over a certain number
)

TWENTY_MINUTE_DATA_ESTIMATE_COEFFICIENT = 0.95
MAX_HEART_RATE_FOR_PREDICTION = 220  # Used for predicting heart rate from age, this is the maximum value for predicting

BUILD_WEEK_RAMP_RATE = 2.5
RECOVERY_WEEK_RAMP_RATE = -2

TOTAL_SESSIONS_NEEDED_TO_UPGRADE_ZONE_DIFFICULTY_LEVEL = 2

BUILD_WEEK_TYPE = "BUILD"
RECOVERY_WEEK_TYPE = "RECOVERY"

MINIMUM_USER_WEIGHT_IN_KG = 20
MAXIMUM_USER_WEIGHT_IN_KG = 300

UTC_TIMEZONE = "+0:00"

LOWEST_PLAN_LENGTH = 28  # days

KNOWLEDGE_HUB_TIP_CRONJOB_TIME = time(0, 5, 0, 0)