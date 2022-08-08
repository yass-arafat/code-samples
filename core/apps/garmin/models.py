from django.db import models

from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.models import CommonFieldModel


class CurveCalculationData(CommonFieldModel):
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="curve_data",
        on_delete=models.CASCADE,
        blank=False,
        null=True,
    )
    user_id = models.UUIDField(null=True)
    source = models.PositiveSmallIntegerField(
        choices=ThirdPartySources.choices(), help_text="Stores source of the activity"
    )
    athlete_activity_code = models.UUIDField(editable=False, null=True)

    activity_datetime = models.DateTimeField(null=True)
    activity_type = models.CharField(
        max_length=55, null=True, help_text="Type of the Activity"
    )

    power_curve = models.TextField(
        null=True, blank=True, help_text="Stores power curve array as string"
    )
    heart_rate_curve = models.TextField(
        null=True, blank=True, help_text="Stores hr curve array as string"
    )

    class Meta:
        db_table = "curve_calculation_data"
        verbose_name = "Curve Calculation Data"
