from django.db import models

from core.apps.common.models import TimeStampedModel


class Activity(TimeStampedModel):
    activity_type = models.CharField(max_length=55, help_text="Type of the Activity")
    activity_sub_type = models.CharField(
        max_length=55, null=True, blank=True, help_text="Sub Type of the Activity"
    )
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel", related_name="pillar_data", on_delete=models.CASCADE
    )
    user_id = models.UUIDField(null=True)

    moving_time_in_seconds = models.IntegerField(
        default=0, help_text="Total time of the activity"
    )

    average_power = models.IntegerField(
        default=0, help_text="Average power during activity", null=True, blank=True
    )
    average_heart_rate = models.IntegerField(
        default=0, help_text="Average heart rate during activity", null=True, blank=True
    )
    average_speed = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Average speed during activity in Km/h",
    )

    total_distance_in_meter = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Total distance covered during activity",
    )

    class Meta:
        db_table = "pillar_data"
        verbose_name = "Pillar Data"

    def __str__(self):
        return (
            "("
            + str(self.id)
            + ") ("
            + self.user_auth.email
            + ") "
            + self.created_at.strftime("%d-%m-%Y (%H:%M:%S)")
        )
