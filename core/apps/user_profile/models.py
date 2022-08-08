from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from config.storage_backends import PrivateMediaStorage
from core.apps.common.models import CommonFieldModel

from ..common.const import (
    MAXIMUM_USER_WEIGHT_IN_KG,
    MINIMUM_USER_WEIGHT_IN_KG,
    TOTAL_SESSIONS_NEEDED_TO_UPGRADE_ZONE_DIFFICULTY_LEVEL,
    UTC_TIMEZONE,
)
from .enums.gender_enum import GenderEnum
from .enums.max_zone_difficulty_level_enum import MaxZoneDifficultyLevel
from .enums.user_access_level_enum import UserAccessLevelEnum
from .enums.user_unit_system_enum import UserUnitSystemEnum
from .managers import TimeZoneManager


class UserProfile(CommonFieldModel):
    name = models.CharField(max_length=50, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(
        null=True, max_length=1, choices=[x.value for x in GenderEnum]
    )
    unit_system = models.CharField(
        max_length=1, choices=[x.value for x in UserUnitSystemEnum]
    )
    allow_notification = models.BooleanField(default=False)
    timezone = models.ForeignKey("TimeZone", on_delete=models.SET_NULL, null=True)
    # user_auth = models.ForeignKey(
    #     "user_auth.UserAuthModel",
    #     related_name="profile_data",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    # )
    user_id = models.UUIDField(null=True)
    access_level = models.CharField(
        max_length=25,
        choices=[x.value for x in UserAccessLevelEnum],
        default=UserAccessLevelEnum.PROFILE.value[0],
        help_text="Defines if the user has completed the onboarding process and can "
        "access the home page of the app or not",
    )

    class Meta:
        db_table = "user_profile"
        verbose_name = "User Profile Table"

    @property
    def full_name(self):
        return f"{self.name} {self.surname}" if self.surname else self.name


class UserPersonaliseData(CommonFieldModel):
    date_of_birth = models.DateField(null=True, blank=True)
    weight = models.DecimalField(
        decimal_places=2, max_digits=20, null=True, blank=True
    )  # will always be in kg format
    training_hours_over_last_4_weeks = models.TextField()
    current_ftp = models.IntegerField(null=True, blank=True)
    current_fthr = models.IntegerField(null=True, blank=True)
    starting_load = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    starting_acute_load = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    starting_prs = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    max_heart_rate = models.IntegerField(null=True, blank=True)
    # user_auth = models.ForeignKey(
    #     "user_auth.UserAuthModel",
    #     related_name="personalise_data",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    # )
    user_id = models.UUIDField(null=True)
    ftp_input_denied = models.BooleanField(default=False)
    fthr_input_denied = models.BooleanField(default=False)

    # Depreciated from R7
    is_power_meter_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]
        db_table = "user_personalise_data"
        verbose_name = "User Personalise Data Table"

    def get_age(self, current_date=None):
        from ..common.utils import get_user_age

        if not self.date_of_birth:
            raise ValueError("No birth date. Failed to calculate user age")

        return (
            get_user_age(self.date_of_birth, current_date)
            if self.date_of_birth
            else None
        )

    @staticmethod
    def is_valid_weight(weight):
        """Checks if the user weight is within valid range"""
        return MINIMUM_USER_WEIGHT_IN_KG <= weight <= MAXIMUM_USER_WEIGHT_IN_KG


class UserScheduleData(models.Model):
    commute_to_work_by_bike = models.BooleanField()
    duration_single_commute_in_hours = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    days_commute_by_bike = models.TextField()
    available_training_hours_per_day_outside_commuting = models.TextField()

    class Meta:
        db_table = "user_schedule_data"
        verbose_name = "User Schedule Data Table"


class UserTrainingAvailability(models.Model):
    commute_to_work_by_bike = models.BooleanField(default=False)
    duration_single_commute_in_hours = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    days_commute_by_bike = models.ForeignKey(
        "user_profile.CommuteWeek",
        related_name="user_training_availabilities",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    available_training_hours_per_day_outside_commuting = models.ForeignKey(
        "user_profile" ".AvailableTrainingDurationsInHour",
        related_name="user_training_availabilities",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="training_availabilities",
        on_delete=models.CASCADE,
    )
    user_id = models.UUIDField(null=True)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_training_availability"
        verbose_name = "User Training Availability Table"

    @property
    def days_commute_by_bike_list(self):
        commute_days = self.days_commute_by_bike
        commute_days_dict = commute_days.__dict__
        ignore_fields = ["_state", "id", "created_at", "updated_at"]
        return [
            value
            for key, value in commute_days_dict.items()
            if key not in ignore_fields
        ]

    @property
    def training_availability_list(self):
        available_hours = self.available_training_hours_per_day_outside_commuting
        available_hours_dict = available_hours.__dict__
        ignore_fields = ["_state", "id", "created_at", "updated_at"]
        return [
            value
            for key, value in available_hours_dict.items()
            if key not in ignore_fields
        ]


class CommuteWeek(models.Model):
    first_day = models.BooleanField(default=False)
    second_day = models.BooleanField(default=False)
    third_day = models.BooleanField(default=False)
    fourth_day = models.BooleanField(default=False)
    fifth_day = models.BooleanField(default=False)
    sixth_day = models.BooleanField(default=False)
    seventh_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commute_by_bike_day"
        verbose_name = "Commute by Bike Day"


class AvailableTrainingDurationsInHour(models.Model):
    first_day_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    second_day_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    third_day_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    fourth_day_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    fifth_day_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    sixth_day_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    seventh_day_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "training_duration"
        verbose_name = "User Available Training Duration Table"


class UserActivityLog(models.Model):
    class ActivityCode(models.IntegerChoices):
        CREATE_TRAINING_PLAN = 1, "Create Training Plan"
        UPDATE_TRAINING_PLAN = 2, "Update Training Plan"
        EMAIL_LOGIN = 3, "User Email Login"
        USER_LOGOUT = 4, "User Logout"
        GARMIN_LOGIN = 5, "User Garmin Login"
        GARMIN_DEREGISTRATION = 6, "Garmin Deregistration"
        GARMIN_CONNECT = 7, "User Garmin Connect"
        GARMIN_DISCONNECT = 8, "User Garmin Disconnect"
        FORGET_PASSWORD = 9, "Forget Password"
        RESET_PASSWORD = 10, "Reset Password"
        EMAIL_CONFIRMATION = 11, "Email Confirmation"
        USER_REGISTRATION = 12, "User Registration"
        GARMIN_ACTIVITY_FILE_SUBMISSION = 13, "Garmin Activity File Submission"
        CORRUPT_GARMIN_ACTIVITY_FILE = 14, "Corrupt Garmin Activity File"
        IGNORED_TYPE_OF_GARMIN_FILE = 15, "Ignored Garmin Activity File"
        SUCCESSFUL_VALID_GARMIN_ACTIVITY_FILE_CALCULATION = (
            16,
            "Valid Garmin Activity File Calculation Successful",
        )
        FAILED_VALID_GARMIN_ACTIVITY_FILE_CALCULATION = (
            17,
            "Valid Garmin Activity File Calculation Failed",
        )
        NOTIFICATION_CREATE = 18, "Notification Creation"
        NOTIFICATION_UPDATE = 19, "Notification History Creation"
        STRAVA_CONNECT = 20, "User Strava Connect"
        STRAVA_DISCONNECT = 21, "User Strava Disconnect"
        SUCCESSFUL_VALID_STRAVA_DATA_CALCULATION = (
            22,
            "Valid Strava Activity Data Calculation Successful",
        )
        PROCESSED_GARMIN_AND_SKIPPED_SESSION_CALCULATION = (
            23,
            "Processed Garmin data and skipped session calculation",
        )
        PROCESSED_STRAVA_AND_SKIPPED_SESSION_CALCULATION = (
            24,
            "Processed Strava data and skipped session calculation",
        )
        HANDLED_STRAVA_UPDATE_REQUEST = 25, "Handled Strava Update Request"
        IGNORED_TYPE_OF_STRAVA_FILE = 26, "Ignored Strava Activity File"
        STRAVA_ACTIVITY_FILE_SUBMISSION = 27, "Strava Activity File Submission"
        AUTO_UPDATE_FAILED_FOR_USER = 28, "Auto update did not run for a user"
        AUTO_UPDATE_SUCCESSFUL_FOR_USER = 29, "Auto update is successful for a user"
        OTP_VERIFICATION = 30, "OTP verification successful"
        OTP_REQUEST = 31, "OTP request to reset password"
        ADD_NEW_GOAL = 32, "Add a new goal for user"
        EDIT_GOAL = 33, "Edit event/goal date"
        USER_SESSION_MOVE = 34, "User Session Move"
        USER_SESSION_DELETE = 35, "User Session Delete"
        USER_PROFILE_UPDATE = 36, "User Profile Update"
        USER_TRAINING_AVAILABILITY_UPDATE = 37, "User Training Availability Update"
        USER_PROFILE_PICTURE_UPDATE = 38, "User Profile Picture Update"
        REFRESH_TOKEN_EXPIRED = 39, "Refresh token expired"
        HISTORICAL_GARMIN_ACTIVITY_REQUEST = (
            40,
            "Backfill request for getting historical Garmin Activities",
        )
        HISTORICAL_STRAVA_ACTIVITY_REQUEST = (
            41,
            "Request for getting historical Strava Activities",
        )
        ADD_MANUAL_ACTIVITY = 42, "Add manual activity"
        DELETE_USER_AWAY_ACTIVITY = 43, "Delete user away"
        ADD_USER_AWAY_ACTIVITY = 44, "ADD user away"
        SYNC_INIT = 45, "APP USER DATA SYNC"
        SESSION_PAIRING = 46, "Pair a completed session with a planned session"
        SESSION_UNPAIRING = 47, "Unpair a evaluated session from a planned session"
        CANCEL_SESSION_PAIRING_MESSAGE = 48, "Cancel session pairing message"
        SESSION_DELETE = 49, "Delete Session"
        SESSION_EDIT = 50, "Edit session"
        SESSION_WARNING_DISMISS = 51, "Session Warning Dismiss"
        SEND_WORKOUT_TO_GARMIN = 52, "Send workout to Garmin"
        USER_ONBOARDING = 53, "User Onboarding"
        USER_SESSION_FEEDBACK = 54, "User Session Feedback"
        DELETE_GOAL = 55, "Delete Goal"
        WEEK_ANALYSIS_REPORT = 56, "Generate Week Analysis Report"
        WEEK_ANALYSIS_FEEDBACK = 57, "Week Analysis Feedback"
        WAHOO_CONNECT = 58, "User Wahoo Connect"
        WAHOO_DISCONNECT = 59, "User Wahoo Disconnect"
        WAHOO_ACTIVITY_FILE_SUBMISSION = 60, "Wahoo Activity File Submission"
        CORRUPT_WAHOO_ACTIVITY_FILE = 61, "Corrupt Wahoo Activity File"
        IGNORED_TYPE_OF_WAHOO_FILE = 62, "Ignored Wahoo Activity File"
        SUCCESSFUL_VALID_WAHOO_ACTIVITY_FILE_CALCULATION = (
            63,
            "Valid Wahoo Activity File Calculation Successful",
        )
        USER_SUPPORT_REQUEST = (
            64,
            "User Support Request",
        )
        SESSION_SUGGEST = 65, "Added Suggested Session"
        EDIT_SINGLE_DAY_AVAILABILITY = 66, "Edit Single Day Availability"
        # When adding new activities, also add
        # in user_activity_code fixture, trainer and Dakghor

    activity_code = models.PositiveSmallIntegerField(choices=ActivityCode.choices)
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="user_activity_logs",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_id = models.UUIDField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    request = models.JSONField(null=True, blank=True)
    response = models.JSONField(null=True, blank=True)
    data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_activity_label(self):
        return self.ActivityCode(self.activity_code).label

    class Meta:
        db_table = "user_activity_log"
        verbose_name = "User Activity Log"
        indexes = [
            models.Index(fields=["activity_code"]),
            models.Index(fields=["user_auth"]),
        ]


class UserActivityType(models.Model):
    class GeneratedBy(models.TextChoices):
        USER = "user", "User"
        SYSTEM = "system", "System"

    activity_name = models.CharField(max_length=255)
    generated_by = models.CharField(
        max_length=55, choices=GeneratedBy.choices, default=GeneratedBy.SYSTEM
    )

    class Meta:
        db_table = "user_activity_type"
        verbose_name = "User Activity Type TT"


class TimeZone(models.Model):
    name = models.CharField(
        max_length=55,
        blank=False,
        null=False,
        default="UTC",
        help_text="Name of a timezone.",
    )
    offset = models.CharField(
        max_length=55,
        blank=False,
        null=False,
        default=UTC_TIMEZONE,
        help_text="Offset of a timezone.",
    )
    offset_second = models.IntegerField(help_text="Offset in second")

    type = models.CharField(max_length=10, blank=False, null=False, default="UTC")
    is_active = models.BooleanField(default=True)

    objects = TimeZoneManager()

    class Meta:
        db_table = "timezone"
        verbose_name = "Timezone Truth Table"


class ProfileImage(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    # user_auth = models.ForeignKey(
    #     "user_auth.UserAuthModel",
    #     related_name="profile_images",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    # )
    user_id = models.UUIDField(null=True)

    avatar = models.ImageField(upload_to="avatars", storage=PrivateMediaStorage())
    avatar_thumbnail = ImageSpecField(
        source="avatar",
        processors=[ResizeToFill(50, 50)],
        format="JPEG",
        options={"quality": 95},
    )
    is_active = models.BooleanField(blank=True, null=True, default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profile_image"
        verbose_name = "User Profile Image Table"


class UserMetaData(CommonFieldModel):
    build_number = models.CharField(
        max_length=255, blank=False, null=False, help_text="User app version"
    )
    hash = models.CharField(
        max_length=255, blank=False, null=False, help_text="User app version"
    )
    device_info = models.JSONField(null=True, blank=True)
    # user_auth = models.ForeignKey(
    #     "user_auth.UserAuthModel", on_delete=models.CASCADE, null=True, blank=True
    # )
    user_id = models.UUIDField(null=True)

    cache_id = models.IntegerField(default=0)

    class Meta:
        db_table = "user_metadata"
        verbose_name = "User MetaData"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ZoneDifficultyLevel(CommonFieldModel):
    # user_auth = models.ForeignKey(
    #     "user_auth.UserAuthModel",
    #     related_name="zone_difficulty_levels",
    #     on_delete=models.CASCADE,
    # )
    user_id = models.UUIDField(null=True)
    zone_three_level = models.SmallIntegerField(default=0)
    zone_four_level = models.SmallIntegerField(default=0)
    zone_five_level = models.SmallIntegerField(default=0)
    zone_six_level = models.SmallIntegerField(default=0)
    zone_seven_level = models.SmallIntegerField(default=0)
    zone_hc_level = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "zone_difficulty_level"
        verbose_name = "Zone Difficulty Level"

    def get_current_level(self, zone_no):
        current_levels = self.get_current_levels()
        for level in current_levels:
            if zone_no == level[0]:
                return level[1]

    def get_current_levels(self):
        return [
            (3, self.zone_three_level),
            (4, self.zone_four_level),
            (5, self.zone_five_level),
            (6, self.zone_six_level),
            (7, self.zone_seven_level),
            ("HC", self.zone_hc_level),
        ]

    @staticmethod
    def is_highest_level(zone_no, level_no):
        return level_no == MaxZoneDifficultyLevel.get_max_level(zone_no)

    @staticmethod
    def is_level_upgradable(session_count):
        return session_count >= TOTAL_SESSIONS_NEEDED_TO_UPGRADE_ZONE_DIFFICULTY_LEVEL

    def is_zone_upgradable(self, zone_no, session_count):
        current_level = self.get_current_level(zone_no)
        if self.is_highest_level(zone_no, current_level):
            return False
        return self.is_level_upgradable(session_count)

    def update_zone_level(self, zone_no):
        if zone_no == 3:
            self.zone_three_level += 1
        elif zone_no == 4:
            self.zone_four_level += 1
        elif zone_no == 5:
            self.zone_five_level += 1
        elif zone_no == 6:
            self.zone_six_level += 1
        elif zone_no == 7:
            self.zone_seven_level += 1
        elif zone_no == "HC":
            self.zone_hc_level += 1

    def set_starting_zone_levels(self, starting_load):
        if starting_load > 50:
            self.zone_three_level = 2
            self.zone_four_level = 2
            self.zone_five_level = 2
            self.zone_six_level = 2
            self.zone_seven_level = 2
        elif starting_load > 25:
            self.zone_three_level = 1
            self.zone_four_level = 1
            self.zone_five_level = 1
            self.zone_six_level = 1
            self.zone_seven_level = 1
        self.zone_hc_level = 0  # Always starts from Level 0

    def reset_all_levels(self):
        self.zone_three_level = 0
        self.zone_four_level = 0
        self.zone_five_level = 0
        self.zone_six_level = 0
        self.zone_seven_level = 0
        self.zone_hc_level = 0
