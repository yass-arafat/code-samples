import datetime
import json
import logging
from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.apps.common.common_functions import CommonClass
from core.apps.common.enums.date_time_format_enum import DateTimeFormatEnum
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.messages import UNPLANNED_SESSION_MESSAGE
from core.apps.common.models import CommonFieldModel, TimeStampedModel
from core.apps.common.utils import get_duplicate_session_timerange
from core.apps.daily.models import PlannedDay
from core.apps.plan.models import UserPlan

from .managers import ActualSessionManager, PlannedSessionManager

logger = logging.getLogger(__name__)


class PlannedSession(models.Model):
    name = models.CharField(max_length=2550)
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="planned_sessions",
        on_delete=models.CASCADE,
        blank=False,
        null=True,
    )
    user_id = models.UUIDField(null=True)
    session_type = models.ForeignKey(
        "session.SessionType",
        related_name="planned_sessions",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    session = models.ForeignKey(
        "session.Session",
        related_name="planned_sessions",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_("session from truth table"),
    )
    pad_time_in_seconds = models.IntegerField(default=0, blank=True, null=True)
    pad_pss = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, blank=True, null=True
    )
    is_pad_applicable = models.BooleanField(default=False, blank=True, null=True)
    zone_focus = models.IntegerField()
    session_date_time = models.DateTimeField()
    day_code = models.UUIDField(
        editable=False, null=True, help_text="Unique day code for each day"
    )
    session_code = models.UUIDField(
        editable=False,
        null=True,
        help_text="Unique Session code for each planned session",
    )

    planned_duration = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    planned_pss = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    planned_load = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    planned_acute_load = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    planned_intensity = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    description = models.TextField(help_text="User Session description")

    planned_time_in_power_zone = models.TextField(
        null=True, blank=True, help_text="Actual Time in zones in power data"
    )
    planned_time_in_hr_zone = models.TextField(
        null=True, blank=True, help_text="Actual Time in zones in heart rate data"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PlannedSessionManager()

    class Meta:
        db_table = "planned_session"
        verbose_name = "User Planned Session Table"

    def __str__(self):
        return (
            "("
            + str(self.id)
            + ") ("
            + self.user_auth.email
            + ") "
            + self.session_date_time.strftime("%d-%m-%Y (%H:%M:%S)")
            + " "
            + self.name
        )

    @property
    def day(self):
        user_day = PlannedDay.objects.filter(
            day_code=self.day_code, is_active=True
        ).last()
        return user_day

    @property
    def is_completed(self):
        actual_session = self.actual_session
        if actual_session:
            if (
                self.is_recovery_session()
                and actual_session.session_score.overall_score == 1
            ):
                return False
            return True
        return False

    @property
    def actual_session(self):
        actual_session = (
            ActualSession.objects.filter(
                session_code=self.session_code,
                is_active=True,
                third_party__isnull=False,
            )
            .order_by("third_party__priority")
            .first()
        )
        if not actual_session and self.is_recovery_session():
            return (
                ActualSession.objects.filter(
                    user_auth=self.user_auth,
                    session_code__isnull=True,
                    session_date_time__date=self.session_date_time.date(),
                    is_active=True,
                )
                .order_by("session_date_time")
                .first()
            )
        return actual_session

    def is_recovery_session(self):
        if self.zone_focus:
            return False
        return True

    @property
    def user_plan(self):
        session_date = self.session_date_time.date()
        user_current_plan = UserPlan.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            start_date__lte=session_date,
            end_date__gte=session_date,
        ).last()
        return user_current_plan

    @staticmethod
    def get_actual_duration(actual_session):
        if actual_session:
            return actual_session.actual_duration / 60
        return 0.0

    @property
    def session_type_name(self):
        if (
            self.is_recovery_session()
            and ActualSession.objects.filter(
                user_auth=self.user_auth,
                is_active=True,
                session_code__isnull=True,
                session_date_time__date=self.session_date_time.date(),
            ).exists()
        ):
            return UNPLANNED_SESSION_MESSAGE
        return self.session_type.name

    @property
    def session_duration(self):
        if self.is_recovery_session():
            unplanned_session = (
                ActualSession.objects.filter(
                    user_auth=self.user_auth,
                    session_code__isnull=True,
                    session_date_time__date=self.session_date_time.date(),
                    is_active=True,
                )
                .order_by("session_date_time")
                .first()
            )
            if unplanned_session:
                return unplanned_session.actual_duration
        return self.planned_duration

    @property
    def is_evaluation_done(self):
        if self.actual_session:
            return True
        return False

    def get_session_duration(self, user):
        if self.is_recovery_session():
            unplanned_session = (
                ActualSession.objects.filter(
                    user_auth=user,
                    session_code__isnull=True,
                    session_date_time__date=self.session_date_time.date(),
                    is_active=True,
                )
                .order_by("session_date_time")
                .first()
            )
            if unplanned_session:
                return unplanned_session.actual_duration
        return self.planned_duration


class SessionScore(TimeStampedModel):
    # Depreciated from R8
    duration_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Duration Score calculated using SQS algorithm",
    )
    sqs_session_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Intensity Score calculated using SQS algorithm",
    )
    sqs_today_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="SQS Today Score calculated using SQS algorithm",
    )
    prs_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="PRS Score calculated using SQS algorithm",
    )
    overall_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Overall Score calculated using SQS algorithm",
    )

    duration_accuracy_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Duration Score calculated using SAS algorithm",
    )
    intensity_accuracy_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Intensity Score calculated using SAS algorithm",
    )
    key_zone_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Key Zone Score calculated using SAS algorithm",
    )
    non_key_zone_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Non Key Zone Score calculated using SAS algorithm",
    )
    sas_today_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="SAS Today Score calculated using SAS algorithm",
    )
    prs_accuracy_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="PRS Score calculated using SAS algorithm",
    )
    overall_accuracy_score = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Overall Score calculated using SAS algorithm",
    )
    key_zone_performance = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )

    pss_score = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)

    class Meta:
        db_table = "session_score"
        verbose_name = "User Session Score Table"

    def get_prs_score(self):
        return round(max(self.prs_score, Decimal(0)))

    def get_prs_accuracy_score(self):
        return round(max(self.prs_accuracy_score, Decimal(0)))

    def get_overall_score(self):
        return round(self.overall_score)

    def get_overall_accuracy_score(self):
        return round(self.overall_accuracy_score)

    def set_overall_accuracy_score(self):
        if self.key_zone_score:
            self.overall_accuracy_score = (
                Decimal(self.duration_accuracy_score) * Decimal(0.25)
                + Decimal(self.intensity_accuracy_score) * Decimal(0.25)
                + Decimal(self.key_zone_score) * Decimal(0.35)
                + Decimal(self.non_key_zone_score) * Decimal(0.15)
            )
        elif self.intensity_accuracy_score:
            self.overall_accuracy_score = Decimal(
                self.duration_accuracy_score
            ) * Decimal(0.5) + Decimal(self.intensity_accuracy_score) * Decimal(0.5)
        else:
            self.overall_accuracy_score = self.duration_accuracy_score

    def get_key_zone_performance_comment(self, key_zone_count: int):
        if not key_zone_count:
            return ""

        if self.key_zone_performance < Decimal(-0.7):
            if key_zone_count > 1:
                return "It looks like you didn't quite spend as much time in the key zones as planned."
            return "It looks like you didn't quite spend as much time in the key zone as planned."
        elif self.key_zone_performance < Decimal(-0.2):
            if key_zone_count > 1:
                return "It looks like you successfully spent time in the key zones but didn't quite meet your target."
            return "It looks like you successfully spent time in the key zone but didn't quite meet your target."
        elif self.key_zone_performance < Decimal(0.2):
            if key_zone_count > 1:
                return "You have done an excellent job at spending time in the key zones as planned!"
            return "You have done an excellent job at spending time in the key zone as planned!"

        if key_zone_count > 1:
            return (
                "It looks like you successfully completed the planned time in the key zones and more, "
                "be careful you are not overtraining."
            )
        return (
            "It looks like you successfully completed the planned time in the key zone and more, "
            "be careful you are not overtraining."
        )

    def get_overall_accuracy_score_label(self):
        if self.overall_accuracy_score > 70:
            return "Excellent"
        elif self.overall_accuracy_score > 40:
            return "Good"
        return "Poor"

    def get_overall_accuracy_score_comment(self):
        if self.overall_accuracy_score > 70:
            return "You did a great job at completing the planned session at the correct intensity."
        elif self.overall_accuracy_score > 40:
            return (
                "You were close to replicating the planned session, "
                "focus on hitting your target intensities in your next session."
            )
        return "It looks like you were not quite able to follow the planned session at the correct intensity."


class ActualSession(CommonFieldModel):
    pillar_data = models.ForeignKey(
        "pillar.Activity",
        related_name="actual_session",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    session_date_time = models.DateTimeField()
    utc_session_date_time = models.DateTimeField(null=True)
    activity_name = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="User given name of the activity",
    )
    session_label = models.CharField(
        max_length=55,
        null=True,
        blank=True,
        default="TRAINING_SESSION",
        help_text="Type of the Activity",
    )
    day_code = models.UUIDField(
        editable=False, null=True, help_text="Unique day code for each day"
    )
    actual_duration = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    actual_pss = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    actual_load = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    actual_acute_load = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    actual_intensity = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    actual_distance_in_meters = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    elevation_gain = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    session_score = models.ForeignKey(
        SessionScore,
        related_name="actual_session",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    session_code = models.UUIDField(
        editable=False,
        null=True,
        help_text="Unique Session code for each planned session",
    )
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="actual_sessions",
        on_delete=models.CASCADE,
        blank=False,
        null=True,
    )
    user_id = models.UUIDField(null=True)
    third_party = models.ForeignKey(
        "settings.ThirdPartySettings",
        related_name="actual_sessions",
        on_delete=models.SET_NULL,
        null=True,
    )
    show_pairing_message = models.BooleanField(default=True)
    description = models.TextField(
        max_length=250,
        blank=True,
        null=True,
        help_text="User's description of the activity",
    )
    effort_level = models.IntegerField(
        help_text="How hard or stressful the activity was for the athlete",
        null=True,
        blank=True,
    )
    show_feedback_popup = models.BooleanField(
        default=True, help_text="If session feedback popup needs to be " "shown or not"
    )
    session_followed_as_planned = models.BooleanField(
        null=True,
        help_text="User input, if the user was able to follow "
        "the session according to the plan or not",
    )
    feedback_option_code = models.IntegerField(
        null=True, help_text="Option code for the predefined feedback options"
    )
    feedback_explanation = models.TextField(
        null=True, help_text="User's explanation about the session"
    )
    code = models.UUIDField(
        editable=False, null=True, help_text="Unique code for each actual session"
    )
    athlete_activity_code = models.CharField(max_length=55, null=True)
    activity_type = models.CharField(max_length=55, null=True)
    reason = models.TextField(
        null=True, help_text="The reason of an actual session row being created"
    )

    actual_intervals = models.JSONField(null=True)

    objects = ActualSessionManager()

    class Meta:
        db_table = "actual_session"
        verbose_name = "User Actual Session Data Table"

    @property
    def planned_session(self):
        if self.session_code:
            return PlannedSession.objects.filter(
                session_code=self.session_code, is_active=True
            ).last()

    @property
    def user_plan(self):
        session_date = self.session_date_time.date()
        user_current_plan = UserPlan.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            start_date__lte=session_date,
            end_date__gte=session_date,
        ).last()
        return user_current_plan

    def is_manual_activity(self):
        return bool(
            self.third_party_id
            and self.third_party.code == ThirdPartySources.MANUAL.value[0]
        )

    def is_recovery_session(self):
        print(f"third-party id {self.third_party_id}")
        if not self.third_party_id:
            return True
        return False

    def is_unplanned_session(self):
        if self.session_code:
            return False
        return True

    def is_part_of_plan(self):
        session_date = self.session_date_time.date()
        user_current_plan = UserPlan.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            start_date__lte=session_date,
            end_date__gte=session_date,
        ).last()
        return bool(user_current_plan)

    def get_sessions_in_timerange_boundary(self):
        """Returns actual_sessions that are in the timerange boundary of current instance and contains same"""
        start_time, end_time = get_duplicate_session_timerange(self.session_date_time)
        return ActualSession.objects.filter(
            user_auth_id=self.user_auth_id,
            session_date_time__range=(start_time, end_time),
            is_active=True,
        ).exclude(id=self.id)

    def is_highest_priority_session(self):
        """Returns whether or not current instance has the highest priority"""
        return (
            not self.get_sessions_in_timerange_boundary()
            .filter(third_party__priority__lte=self.third_party.priority)
            .exists()
        )

    def get_planned_session_from_list(self, planned_sessions):
        return planned_sessions.filter(session_code=self.session_code).last()

    # TODO: Remove below functions in R11
    @property
    def get_activity_type(self):
        activity_type = self.ride_data.activity_type if self.ride_data_id else None
        if not activity_type and self.is_manual_activity():
            activity_type = self.pillar_data.activity_type
        return activity_type

    @property
    def ride_data(self):
        return self.garmin_data or self.strava_data

    @property
    def ride_data_id(self):
        return self.garmin_data_id or self.strava_data_id


def get_session_from_session_date(session_date, plan_id):
    # https://stackabuse.com/converting-strings-to-datetime-in-python/

    session_date_time_start_date_str = session_date + " 00:00:00.0000"
    session_date_time__start_date_obj = datetime.datetime.strptime(
        session_date_time_start_date_str, DateTimeFormatEnum.app_date_time_format.value
    )

    session_date_time_end_date_str = session_date + " 23:59:59.0000"
    session_date_time__end_date_obj = datetime.datetime.strptime(
        session_date_time_end_date_str, DateTimeFormatEnum.app_date_time_format.value
    )
    try:
        session = PlannedSession.objects.filter(
            session_date_time__range=(
                session_date_time__start_date_obj,
                session_date_time__end_date_obj,
            ),
            plan_id=plan_id,
            is_active=True,
        )

    except Exception as e:
        logger.exception(str(e))
        session = None
    return session


def get_session_for_month(start_date, end_date, plan_id):
    try:
        session_list = PlannedSession.objects.filter(
            plan_id=plan_id,
            is_active=True,
            session_date_time__range=(start_date, end_date),
        )

    except Exception as e:
        logger.exception(str(e) + "Session List not found")
        session_list = None

    return session_list


def change_status(session_id, status):
    try:
        session = PlannedSession.objects.get(id=session_id, is_active=True)
        session.is_completed = status
        session.save()
    except Exception as e:
        logger.exception(str(e) + "Couldn't update session status")
        session = None
    return session


class SessionInterval(models.Model):
    session = models.ForeignKey(
        "session.Session",
        related_name="session_intervals",
        on_delete=models.CASCADE,
        null=True,
    )
    name = models.CharField(max_length=550, default="N")
    time_in_seconds = models.IntegerField(default=0)
    ftp_percentage_lower = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    ftp_percentage_upper = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    fthr_percentage_lower = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    fthr_percentage_upper = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    mhr_percentage_lower = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    mhr_percentage_upper = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    rpe_lower = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    rpe_upper = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    cadence_lower = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    cadence_upper = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    pss = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    is_padding_interval = models.BooleanField(default=False)
    key_interval_tag = models.BooleanField(null=True)

    class Meta:
        db_table = "session_interval"
        verbose_name = "Session Interval TT"

    def __str__(self):
        return "(" + str(self.id) + ") " + self.session.code + ": " + self.name

    @property
    def mid_ftp(self):
        return (self.ftp_percentage_upper + self.ftp_percentage_lower) / 2

    @property
    def mid_fthr(self):
        if self.fthr_percentage_upper == 999:
            return self.fthr_percentage_lower
        return (self.fthr_percentage_lower + self.fthr_percentage_upper) / 2

    @property
    def mid_max_heart_rate(self):
        if self.mhr_percentage_upper == 999:
            return self.mhr_percentage_lower
        return (self.mhr_percentage_lower + self.mhr_percentage_upper) / 2

    @property
    def power_zone_focus(self):
        return CommonClass.get_zone_focus_from_ftp(self.mid_ftp)

    @property
    def heart_rate_zone_focus(self):
        return CommonClass.get_zone_focus_from_fthr(self.mid_fthr)

    def get_hr_from_fthr(self, user_fthr):
        return (self.mid_fthr / 100) * user_fthr

    def get_hr_from_max_heart_rate(self, max_heart_rate):
        return (self.mid_max_heart_rate / 100) * max_heart_rate


class SessionType(models.Model):
    name = models.CharField(max_length=550)
    rule = models.ForeignKey(
        "session.SessionRules",
        related_name="session_types",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=100, null=True)
    target_zone = models.IntegerField(null=True)
    number_of_sessions = models.IntegerField(null=True)
    average_intensity = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )

    class Meta:
        db_table = "session_type"
        verbose_name = "Session Type TT"

    def __str__(self):
        return "(" + str(self.id) + ") " + self.code

    def get_zone_focus(self):
        """Only use it when HC is needed"""
        if self.code == "HC":
            return "HC"
        return self.target_zone


class Session(models.Model):
    code = models.CharField(max_length=550)
    session_type = models.ForeignKey(
        "session.SessionType",
        related_name="sessions",
        on_delete=models.CASCADE,
        null=True,
    )
    title = models.CharField(max_length=550)
    description = models.TextField()
    duration_in_minutes = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )
    intensity = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )
    pss = models.DecimalField(decimal_places=2, max_digits=20, default=0.00, null=True)
    difficulty_level = models.SmallIntegerField(null=True)
    key_zones = models.TextField(null=True)

    is_active = models.BooleanField(_("Active"), default=True)

    def get_key_zone_description(self, key_zones=None):
        if not key_zones:
            key_zones = json.loads(self.key_zones)

        if not key_zones:
            return ""
        elif len(key_zones) == 1:
            return f"The key zone for this session was Zone {key_zones[0]}"
        description = "The key zones for this session were " + ", ".join(
            [f"Zone {zone}" for zone in key_zones[:-1]]
        )
        description += f" and Zone {key_zones[-1]}"
        return description

    class Meta:
        db_table = "session"
        verbose_name = "Session TT"

    def __str__(self):
        return "(" + str(self.id) + ") (" + self.code + ") " + self.title


class SessionRules(models.Model):
    zone_focus = models.IntegerField(null=True)
    typical_intensity = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )
    minimum_pss = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00, null=True
    )
    max_num_of_selected_session_type_per_week = models.IntegerField(null=True)

    class Meta:
        db_table = "session_rules"
        verbose_name = "Session Rules"


def create_actual_session(day_obj, activity_datetime, utc_activity_datetime, user_auth):
    session = ActualSession()
    session.session_date_time = activity_datetime
    session.utc_session_date_time = utc_activity_datetime
    session.user_auth = user_auth
    session.user_id = user_auth.code
    session.day_code = day_obj.day_code if day_obj else None

    return session


class UserAway(models.Model):
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="user_away_days",
        on_delete=models.CASCADE,
    )
    user_id = models.UUIDField(null=True)
    away_date = models.DateField(blank=True, null=True)
    interval_code = models.UUIDField(
        editable=False, null=True, blank=True, help_text="away interval code"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_away"
        verbose_name = "User Away"

    def __str__(self):
        return (
            "("
            + str(self.id)
            + ") ("
            + self.away_date.strftime("%Y-%m-%d")
            + ") "
            + self.user_auth.email
        )


class UserAwayInterval(models.Model):
    interval_code = models.UUIDField(
        editable=False, null=True, blank=True, help_text="away interval code"
    )
    reason = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_away_interval"
        verbose_name = "User Away Intervals"


class SessionFeedbackOption(models.Model):
    option_code = models.IntegerField(
        help_text="Unique integer code for the available feedback options"
    )
    option_text = models.CharField(
        max_length=255, help_text="Feedback option description"
    )

    class Meta:
        db_table = "session_feedback_option"
        verbose_name = "Session Feedback Options"
