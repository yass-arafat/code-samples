import datetime
import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.apps.common.const import STARTING_SAS, STARTING_SQS
from core.apps.common.models import CommonFieldModel
from core.apps.common.utils import get_obj_recovery_index, get_rounded_freshness
from core.apps.daily.managers import ActualDayManager, PlannedDayManager
from core.apps.week.models import UserWeek

logger = logging.getLogger(__name__)


class UserDay(models.Model):
    SQS_CHOICES = [("STARTING_SQS", STARTING_SQS), ("STARTING_SAS", STARTING_SAS)]

    class DayChangingReason(models.IntegerChoices):
        FIT_FILE_UPLOADED = 1, "Fit file upload"
        MORNING_CRONJOB = 2, "Morning calculation"
        MIDNIGHT_CRONJOB = 3, "Midnight calculation"
        AUTO_UPDATE_PLAN = 4, "Auto update training plan"

    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="user_days",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_id = models.UUIDField(null=True)
    user_week = models.ForeignKey(
        "week.UserWeek",
        related_name="user_days",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_("week of this day"),
    )
    activity_date = models.DateField()
    max_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
    )

    training_pss_by_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS load approach",
    )
    training_pss_by_freshness = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS freshness approach",
    )
    training_pss_by_max_ride = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS max load approach",
    )
    training_pss_by_hours = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS max hours approach",
    )
    training_pss_final_value = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="minimum of four different pss",
    )

    planned_load = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    planned_acute_load = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    planned_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual load of a user in day",
    )
    actual_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual load of a user in day",
    )
    actual_acute_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual acute load of a user in day",
    )
    actual_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual pss of a user in day",
    )
    load_post_commute = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Load post commute for day n",
    )
    acute_load_post_commute = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Acute Load post commute for day n",
    )
    zone_focus = models.IntegerField(default=0)
    commute_pss_day = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="commute pss of a user in day",
    )

    recovery_index = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    prs_score = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    sqs_today = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    overall_score = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    day_code = models.UUIDField(
        editable=False, null=True, help_text="Unique day code for each day"
    )
    week_code = models.UUIDField(
        editable=False, null=True, help_text="Unique week code for each week"
    )
    reason = models.PositiveSmallIntegerField(
        choices=DayChangingReason.choices, null=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_day"
        verbose_name = "User Day Table"

    def __str__(self):
        return (
            "("
            + str(self.id)
            + ") ("
            + self.user_auth.email
            + ") "
            + self.activity_date.strftime("%d-%m-%Y")
        )

    @property
    def previous_day(self):
        previous_day = UserDay.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            activity_date=(self.activity_date - datetime.timedelta(days=1)),
        )
        if previous_day:
            return previous_day[0]
        else:
            return None

    @property
    def next_day(self):
        next_day = UserDay.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            activity_date=(self.activity_date + datetime.timedelta(days=1)),
        )
        if next_day:
            return next_day[0]
        else:
            return None

    @property
    def week(self):
        user_week = UserWeek.objects.get(week_code=self.week_code, is_active=True)
        return user_week


class PlannedDay(CommonFieldModel):
    SQS_CHOICES = [("STARTING_SQS", STARTING_SQS), ("STARTING_SAS", STARTING_SAS)]

    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="planned_days",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_id = models.UUIDField(null=True)

    activity_date = models.DateField()
    max_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
    )

    training_pss_by_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS load approach",
    )
    training_pss_by_freshness = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS freshness approach",
    )
    training_pss_by_max_ride = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS max load approach",
    )
    training_pss_by_hours = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Training PSS max hours approach",
    )
    training_pss_final_value = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="minimum of four different pss",
    )

    planned_load = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    planned_acute_load = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    planned_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual load of a user in day",
    )

    load_post_commute = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Load post commute for day n",
    )
    acute_load_post_commute = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Acute Load post commute for day n",
    )
    zone_focus = models.IntegerField(default=0)
    commute_pss_day = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="commute pss of a user in day",
    )

    day_code = models.UUIDField(
        editable=False, null=True, help_text="Unique day code for each day"
    )
    week_code = models.UUIDField(
        editable=False, null=True, help_text="Unique week code for each week"
    )

    objects = PlannedDayManager()

    class Meta:
        db_table = "planned_day"
        verbose_name = "Planned Day Table"

    def __str__(self):
        return (
            "("
            + str(self.id)
            + ") ("
            + self.user_auth.email
            + ") "
            + self.activity_date.strftime("%d-%m-%Y")
        )

    @property
    def previous_day(self):
        previous_day = PlannedDay.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            activity_date=(self.activity_date - datetime.timedelta(days=1)),
        )
        if previous_day:
            return previous_day[0]
        else:
            return None

    @property
    def next_day(self):
        next_day = PlannedDay.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            activity_date=(self.activity_date + datetime.timedelta(days=1)),
        )
        if next_day:
            return next_day[0]
        else:
            return None

    @property
    def week(self):
        user_week = UserWeek.objects.get(week_code=self.week_code, is_active=True)
        return user_week


class ActualDay(CommonFieldModel):
    SQS_CHOICES = [("STARTING_SQS", STARTING_SQS), ("STARTING_SAS", STARTING_SAS)]

    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="actual_days",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_id = models.UUIDField(null=True)
    activity_date = models.DateField()

    actual_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual load of a user in day",
    )
    actual_acute_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual acute load of a user in day",
    )

    actual_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual pss of a user in day",
    )

    zone_focus = models.IntegerField(default=0, null=True)

    recovery_index = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )
    day_code = models.UUIDField(
        editable=False, null=True, help_text="Unique day code for each day"
    )
    week_code = models.UUIDField(
        editable=False, null=True, help_text="Unique week code for each week"
    )

    prs_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        null=True,
        help_text="PRS Score calculated using SQS_today",
    )
    sqs_today = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )

    prs_accuracy_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        null=True,
        help_text="PRS Score calculated using SAS_today",
    )
    sas_today = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )
    reason = models.TextField(
        null=True, help_text="The reason of a specific actual day row being created"
    )

    objects = ActualDayManager()

    class Meta:
        db_table = "actual_day"
        verbose_name = "Actual Day Table"

    @property
    def actual_freshness(self):
        return get_rounded_freshness(self.actual_load, self.actual_acute_load)

    def set_data_from_actual_session(self, actual_session):
        if not actual_session:
            return

        self.actual_load = actual_session.actual_load
        self.actual_acute_load = actual_session.actual_acute_load
        session_score = actual_session.session_score
        if session_score:
            self.sqs_today = session_score.sqs_today_score
            self.sas_today = session_score.sas_today_score
            self.prs_score = session_score.prs_score
            self.prs_accuracy_score = session_score.prs_accuracy_score

        self.recovery_index = get_obj_recovery_index(actual_session)

    def set_data_from_planned_day(self, planned_day):
        if not planned_day:
            return

        self.week_code = planned_day.week_code
        self.day_code = planned_day.day_code
        self.zone_focus = planned_day.zone_focus
