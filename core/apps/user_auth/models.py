import logging
from datetime import datetime, timedelta

from django.db import models

from core.apps.user_profile.avatar import get_avatar

from ..activities.utils import dakghor_get_athlete_info
from ..common.date_time_utils import DateTimeUtils
from .managers import OtpManager, UserAuthModelManager

logger = logging.getLogger(__name__)


class UserAuthModel(models.Model):
    email = models.EmailField("email address", unique=True, blank=True, null=True)
    password = models.CharField(max_length=255, default=None, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    registration_type = models.IntegerField(default=1)
    # activation_token = models.CharField(max_length=255, default=None, blank=True, null=True)
    access_token = models.CharField(max_length=255, default=None, blank=True, null=True)
    access_token_expires_at = models.CharField(max_length=255, blank=True, null=True)
    refresh_token = models.CharField(
        max_length=255, default=None, blank=True, null=True
    )
    refresh_token_expires_at = models.CharField(max_length=255, blank=True, null=True)
    code = models.UUIDField(null=True)
    strava_user_token = models.CharField(
        max_length=255, default=None, blank=True, null=True
    )
    strava_user_id = models.CharField(max_length=255, blank=True, null=True)
    strava_refresh_token = models.CharField(max_length=255, blank=True, null=True)
    strava_token_expires_at = models.CharField(max_length=255, blank=True, null=True)
    strava_user_name = models.CharField(max_length=255, blank=True, null=True)
    garmin_user_token = models.CharField(
        max_length=255, default=None, blank=True, null=True
    )
    garmin_user_secret = models.CharField(
        max_length=255, default=None, blank=True, null=True
    )
    garmin_user_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateField(auto_now_add=True, help_text="user onboarding date")
    updated_at = models.DateField(auto_now=True, help_text="user info updating date")
    schedule_data = models.OneToOneField(
        "user_profile.UserScheduleData", on_delete=models.CASCADE, null=True, blank=True
    )

    objects = UserAuthModelManager()

    class Meta:
        db_table = "user_auth"
        verbose_name = "User Authentication Table"

    def __str__(self):
        return f"{self.id} - {self.email} - {self.code}"

    # deleting api_token to corresponding user
    def remove_access_token(self):
        self.access_token = None
        try:
            self.save()
        except Exception as e:
            logger.exception(str(e) + "Couldn't save user")

    def is_garmin_connected(self):
        """Check if the user is currently connected with Garmin"""

        if self.garmin_user_token:
            return True
        return False

    def is_strava_connected(self):
        """Check if the user is currently connected with Strava"""

        if self.strava_user_token:
            return True
        return False

    def is_third_party_connected(self):
        """Check if the user is currently connected with any third party"""
        user_info = dakghor_get_athlete_info(self.code)
        return (
            True
            if user_info["is_garmin_connected"]
            or user_info["is_strava_connected"]
            or user_info["is_wahoo_connected"]
            else False
        )

    def get_profile_picture(self):
        profile_image = self.profile_images.filter(is_active=True).first()
        if profile_image:
            return profile_image.avatar.url
        return get_avatar()

    def is_onboarding_week(self, current_date):
        first_plan = self.user_plans.first()
        if first_plan is None:
            return False
        week_start_date = current_date - timedelta(current_date.weekday())
        return first_plan.start_date >= week_start_date

    @property
    def timezone_offset(self):
        timezone_offset = (
            self.profile_data.filter(is_active=True).values("timezone__offset").last()
        )
        return timezone_offset["timezone__offset"] if timezone_offset else None

    @property
    def user_local_date(self):
        """Returns user's current date in local timezone"""
        return DateTimeUtils.get_user_local_date_from_utc(
            self.timezone_offset, datetime.now()
        )


class Otp(models.Model):
    otp = models.IntegerField(blank=True, null=True)
    email = models.EmailField("email address", blank=True, null=True)
    verifier_token = models.CharField(max_length=255, blank=True, null=True)
    access_token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text="otp creation date")
    updated_at = models.DateTimeField(auto_now=True, help_text="otp updating date")

    objects = OtpManager()

    class Meta:
        db_table = "otp"
        verbose_name = "OTP Table"
