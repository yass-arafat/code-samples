from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.common.models import CommonFieldModel


class RecordType(models.Model):
    name = models.CharField(
        max_length=55, null=True, help_text="Name of the Record Type e.g. Longest Ride"
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        db_table = "record_type"
        verbose_name = "Record Type"


class RecordLevel(models.Model):
    record_type = models.ForeignKey(
        RecordType, related_name="record_levels", on_delete=models.CASCADE
    )
    level = models.IntegerField(
        help_text="Indicates specific level of a particular record type"
    )
    required_value = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        help_text="Required threshold value for achieving a level",
    )
    unit = models.CharField(
        max_length=25,
        null=True,
        help_text="Unit of the required value to achieve a level",
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        db_table = "record_level"
        verbose_name = "Record Level"


class PersonalRecord(CommonFieldModel):
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="personal_records",
        on_delete=models.CASCADE,
    )
    user_id = models.UUIDField(null=True)
    record_type = models.ForeignKey(
        RecordType, related_name="personal_records", on_delete=models.CASCADE
    )
    record_level = models.ForeignKey(
        RecordLevel, related_name="personal_records", on_delete=models.CASCADE
    )
    actual_session_code = models.UUIDField(
        editable=False,
        help_text="Needed for referring to the corresponding actual session",
    )

    class Meta:
        db_table = "personal_record"
        verbose_name = "Personal Record"
