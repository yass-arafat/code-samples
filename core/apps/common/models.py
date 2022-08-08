import json

from django.db import models
from django.utils.translation import gettext_lazy as _


class CronHistoryLog(models.Model):
    class CronCode(models.IntegerChoices):
        MIDNIGHT_CALCULATION = 1, "Midnight Calculation"
        MORNING_CALCULATION = 2, "Morning Calculation"
        AUTO_UPDATE_TRAINING_PLAN = 3, "Auto Update Training Plan"
        UPDATE_USER_SETTINGS = 4, "Update User Settings"
        UPDATE_TODAY_NOTIFICATION = 5, "Update Today Notification For User"
        WEEK_ANALYSIS = 6, "Week Analysis Report"
        KNOWLEDGE_HUB_TIP = 7, "Knowledge Hub Tip"

    class StatusCode(models.IntegerChoices):
        SUCCESSFUL = 1, "Successful"
        FAILED = 2, "Failed"

    cron_code = models.PositiveSmallIntegerField(choices=CronCode.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_auth = models.ForeignKey("user_auth.UserAuthModel", on_delete=models.CASCADE)
    user_id = models.UUIDField(null=True)
    status = models.PositiveSmallIntegerField(choices=StatusCode.choices)

    class Meta:
        db_table = "cron_history_log"
        verbose_name = "Cron History Log"


class TimeStampedModel(models.Model):
    """
    TimeStampedModel
    An abstract base class model that provides self-managed "created_at" and
    "updated_at" fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CommonFieldModel(TimeStampedModel):

    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        abstract = True


class PillarData(models.Model):
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_type = models.CharField(
        max_length=55, null=True, blank=True, help_text="Type of The File"
    )
    activity_type = models.CharField(
        max_length=55, null=True, blank=True, help_text="Type of the Activity"
    )
    activity_sub_type = models.CharField(
        max_length=55, null=True, blank=True, help_text="Sub Type of the Activity"
    )

    moving_time_in_seconds = models.IntegerField(
        default=0, help_text="Time where speed is not 0 and power is not 0"
    )
    elapsed_time_in_seconds = models.IntegerField(
        default=0, help_text="Total time of the activity"
    )

    second_by_second_time = models.TextField(
        null=True,
        blank=True,
        help_text="Second by Second elapsed time in seconds "
        "from start of the activity",
    )
    second_by_second_power = models.TextField(
        null=True, blank=True, help_text="Activity Fit File Second by Second Power data"
    )
    second_by_second_hr = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second heart rate data",
    )
    second_by_second_speed = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second heart rate data",
    )
    second_by_second_cadence = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second Cadence data",
    )
    second_by_second_temperature = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second Temperature data",
    )
    second_by_second_latitude = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second Latitude data",
    )
    second_by_second_longitude = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second Longitude data",
    )
    second_by_second_elevation = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second Elevation data",
    )
    second_by_second_distance = models.TextField(
        null=True,
        blank=True,
        help_text="Activity Fit File Second by Second Distance data",
    )
    elevation_gain = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Elevation gain during an activity",
    )
    actual_time_in_power_zone = models.TextField(
        null=True, blank=True, help_text="Actual Time in zones in power data"
    )
    actual_time_in_hr_zone = models.TextField(
        null=True, blank=True, help_text="Actual Time in zones in heart rate data"
    )
    moving_fraction = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Moving fraction of an activity",
    )
    weighted_power = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    total_power = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Total power during activity",
    )
    total_heart_rate = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Total heart rate during activity",
    )
    total_distance_in_meter = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Total distance covered during activity",
    )

    ride_summary = models.TextField(
        null=True, blank=True, help_text="User ride Summary"
    )
    """
    If the difference between pillar calculated and third party data is more than the threshold value for that
    specific attribute, then the third party data will be saved in the ride summary and pillar calculated value
    will be stored in flagged values.
    """
    flagged_values = models.TextField(
        null=True, blank=True, help_text="The values which are flagged"
    )

    class Meta:
        abstract = True

    def get_ride_summary(self):
        selected_ride_summary = []
        if self.ride_summary:
            types = ["Heart Rate", "Power", "Speed", "Cadence"]
            decimal_places = {"Heart Rate": 0, "Power": 0, "Speed": 1, "Cadence": 0}

            self.ride_summary = self.ride_summary.replace("'", '"')
            ride_summaries = json.loads(self.ride_summary)

            for ride_summary in ride_summaries:
                if ride_summary["type"] in types:
                    if decimal_places[ride_summary["type"]]:
                        ride_summary["average"] = round(
                            ride_summary["average"],
                            decimal_places[ride_summary["type"]],
                        )
                        ride_summary["max"] = round(
                            ride_summary["max"], decimal_places[ride_summary["type"]]
                        )
                    else:
                        ride_summary["average"] = round(ride_summary["average"])
                        ride_summary["max"] = round(ride_summary["max"])
                    selected_ride_summary.append(ride_summary)

        return selected_ride_summary

    def get_ride_summary_v2(self):
        ride_summaries = self.get_ride_summary()
        for ride_summary in ride_summaries:
            ride_summary["average"] = (
                str(ride_summary["average"]) if ride_summary["average"] else None
            )
            ride_summary["max"] = (
                str(ride_summary["max"]) if ride_summary["max"] else None
            )
        return ride_summaries
