import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.apps.common.const import BUILD_WEEK_TYPE, RECOVERY_WEEK_TYPE
from core.apps.common.models import CommonFieldModel

from .managers import WeekAnalysisManager

logger = logging.getLogger(__name__)


class UserWeek(models.Model):
    WEEK_TYPE_CHOICES = [
        (BUILD_WEEK_TYPE, "Build week"),
        (RECOVERY_WEEK_TYPE, "Recovery week"),
    ]

    session_type = models.ForeignKey(
        "session.SessionType",
        related_name="user_weeks",
        on_delete=models.CASCADE,
        help_text=_("session type of the week"),
        null=True,
        blank=True,
    )
    user_block = models.ForeignKey(
        "block.UserBlock",
        related_name="user_weeks",
        on_delete=models.CASCADE,
        help_text=_("block of this week"),
    )
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="user_weeks",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    user_id = models.UUIDField(null=True)
    start_date = models.DateField(
        blank=True, null=True, help_text=_("start date of the week")
    )
    end_date = models.DateField(
        blank=True, null=True, help_text=_("end date of the week")
    )
    week_type = models.CharField(
        max_length=20,
        choices=WEEK_TYPE_CHOICES,
        default="BUILD",
        help_text=_("type of week"),
    )
    zone_focus = models.IntegerField(
        default=0, help_text=_("zone focus value for this week")
    )
    sunday_max_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text=_("calculated max load for last sunday of this week"),
    )
    actual_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual load of a user in week",
    )
    actual_acute_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual acute load of a user in week",
    )
    actual_freshness = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual freshness of a user in a week",
    )
    actual_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual pss of a user in week",
    )
    commute_pss_week = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="commute pss of a user in week",
    )

    planned_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual load of a user in week",
    )
    week_code = models.UUIDField(
        editable=False, null=True, help_text="Unique week code for each week"
    )
    block_code = models.UUIDField(editable=False, null=True, help_text="Unique block")

    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        db_table = "user_week"
        verbose_name = "User Week Table"

    def __str__(self):
        block_no = "Block: " + str(self.user_block.number)
        user = str(self.user_block.user_auth)
        return "(" + str(self.id) + ") (" + block_no + ") " + self.week_type + user


class WeekRules(models.Model):
    priority_number = models.IntegerField(null=True)
    zone_focus = models.IntegerField(null=True)
    session_type = models.ForeignKey(
        "session.SessionType", on_delete=models.CASCADE, null=True
    )

    class Meta:
        db_table = "week_rules"
        verbose_name = "Week Rules"


class WeekAnalysis(CommonFieldModel):
    GREAT = "GREAT"
    OK = "OK"
    HARD = "HARD"
    FEEL_FEEDBACK_CHOICES = (
        (GREAT, _("Great")),
        (OK, _("Ok")),
        (HARD, _("Hard")),
    )

    user_id = models.UUIDField()
    code = models.UUIDField(help_text="Unique code for each week analysis")

    report_date = models.DateField()

    week_no = models.IntegerField(null=True)
    total_weeks_in_block = models.IntegerField(null=True)
    week_title = models.CharField(max_length=255)
    week_start_date = models.DateField()
    week_end_date = models.DateField()

    distance = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.0, help_text="Distance in meters"
    )
    duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.0, help_text="Duration in minutes"
    )
    elevation = models.IntegerField(help_text="Elevation in meters", default=0)
    total_rides = models.IntegerField(default=0)
    pss = models.IntegerField(default=0)

    current_week_remarks = models.JSONField(null=True)
    last_week_comparison_remarks = models.JSONField(null=True)
    tips_for_next_week = models.JSONField(null=True)

    is_ftp_available = models.BooleanField()
    is_fthr_available = models.BooleanField()
    actual_time_in_power_zones = models.JSONField()
    planned_time_in_power_zones = models.JSONField()
    actual_time_in_hr_zones = models.JSONField()
    planned_time_in_hr_zones = models.JSONField()

    feel_feedback = models.CharField(
        max_length=10, choices=FEEL_FEEDBACK_CHOICES, null=True
    )
    week_feedback = models.CharField(max_length=255, null=True)
    suggestion_feedback = models.CharField(max_length=255, null=True)

    utp_summary = models.JSONField()
    utp_reason = models.JSONField()

    average_sas = models.FloatField(default=0.0)
    actual_time_in_zone = models.IntegerField(default=0)
    actual_time_above_zone = models.IntegerField(default=0)

    objects = WeekAnalysisManager()

    class Meta:
        db_table = "week_analysis"
        verbose_name = "Week Analysis"

    def is_feedback_saved(self):
        feel_feedback = self.feel_feedback
        week_feedback = self.week_feedback
        suggestion_feedback = self.suggestion_feedback
        is_feedback_saved = not bool(
            feel_feedback is None
            and week_feedback is None
            and suggestion_feedback is None
        )

        return is_feedback_saved
