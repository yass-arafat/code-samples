import datetime
import logging
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Sum

from core.apps.block.models import UserBlock
from core.apps.common.date_time_utils import convert_second_to_str
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.models import CronHistoryLog
from core.apps.common.utils import (
    create_new_model_instance,
    dakghor_get_time_in_zones,
    initialize_dict,
    log_extra_fields,
)
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.evaluation.session_evaluation.utils import (
    add_time_in_zones,
    is_time_spent_in_zone,
)
from core.apps.session.models import ActualSession, PlannedSession
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.models import UserPersonaliseData, ZoneDifficultyLevel

from ..activities.pillar.utils import get_max_cadence_from_ride_summary
from ..activities.utils import dakghor_get_athlete_activity
from .enums.week_analysis_report_enums import (
    WeekAnalysisReportTitle,
    WeekAnalysisUTPReason,
    WeekAnalysisUTPSummary,
    WeekAnalysisWeekRemarks,
    WeekAnalysisZoneDescription,
)
from .models import UserWeek, WeekAnalysis

logger = logging.getLogger(__name__)


class WeekAnalysisFeedbackService:
    def __init__(self, user, data):
        self.user = user
        self.data = data

    def save_weekly_analysis_feedback(self):
        week_analysis = WeekAnalysis.objects.filter_active(
            user_id=self.user.code, code=self.data.get("id")
        ).last()

        self._check_validation(week_analysis)

        week_analysis.feel_feedback = self.data.get("feel_feedback")
        week_analysis.week_feedback = self.data.get("week_feedback")
        week_analysis.suggestion_feedback = self.data.get("suggestion_feedback")
        week_analysis = create_new_model_instance(week_analysis)
        week_analysis.save()

        return week_analysis

    def _check_validation(self, week_analysis):
        if self.data.get("id") is None:
            raise ValidationError(f"No week analysis code provided. data: {self.data}")

        if week_analysis is None:
            raise ValidationError(f"No week analysis found. data: {self.data}")

        if week_analysis.is_feedback_saved():
            raise ValidationError("Feedback is already saved")


class WeekAnalysisRemarks:
    def __init__(
        self,
        user_auth,
        user_local_date,
        start_date,
        end_date,
        zone_focus,
        zone_description,
        actual_sessions,
        duration,
        total_rides: int,
        actual_time_in_zones,
        planned_time_in_zones,
    ):
        self.user_auth = user_auth
        self.user_local_date = user_local_date
        self.start_date = start_date
        self.end_date = end_date
        self.zone_focus = zone_focus
        self.zone_description = zone_description
        self.actual_sessions = actual_sessions
        self.planned_sessions = PlannedSession.objects.filter(
            session_date_time__range=(self.start_date, self.end_date),
            is_active=True,
            user_auth=self.user_auth,
        )
        self.duration = duration
        self.total_rides = total_rides
        self.actual_time_in_zones = actual_time_in_zones
        self.planned_time_in_zones = planned_time_in_zones
        self.previous_week_analysis = WeekAnalysis.objects.filter(
            user_id=self.user_auth.code, is_active=True
        ).last()

        self.average_sas = 0
        self.actual_time_in_zone = 0
        self.planned_time_in_zone = 0
        self.actual_time_above_zone = 0
        self.planned_time_above_zone = 0
        self.starting_zone_difficulty_level = None
        self.ending_zone_difficulty_level = None
        self.total_paired_sessions = None
        self.total_planned_sessions = None
        self.total_better_scored_paired_sessions = None
        self.days_since_last_unpaired = None

    def get_remarks(self):
        self._set_stats()
        return {
            "average_sas": self.average_sas,
            "actual_time_in_zone": self.actual_time_in_zone,
            "actual_time_above_zone": self.actual_time_above_zone,
            "current_week_remarks": self._get_this_week_remarks(),
            "last_week_comparison_remarks": self._get_last_week_comparison_remarks(),
            "tips_for_next_week": self._get_tips_for_next_week(),
        }

    def _set_stats(self):
        for time_in_zone in self.actual_time_in_zones:
            if time_in_zone["zone"] == self.zone_focus:
                self.actual_time_in_zone = time_in_zone["value"]
            if time_in_zone["zone"] > self.zone_focus:
                self.actual_time_above_zone += time_in_zone["value"]
        for time_in_zone in self.planned_time_in_zones:
            if time_in_zone["zone"] == self.zone_focus:
                self.planned_time_in_zone = time_in_zone["value"]
            if time_in_zone["zone"] > self.zone_focus:
                self.planned_time_above_zone += time_in_zone["value"]

        self.starting_zone_difficulty_level = self._get_zone_difficulty_level(
            self.start_date
        )
        self.ending_zone_difficulty_level = self._get_zone_difficulty_level(
            self.end_date
        )
        self.total_paired_sessions = ActualSession.objects.filter_actual_sessions(
            user_auth=self.user_auth,
            session_code__in=self._get_planned_sessions_codes(),
        ).count()

        self.total_planned_sessions = self.planned_sessions.exclude(
            zone_focus=0
        ).count()
        self.days_since_last_unpaired = self._get_days_since_last_unpaired()

        self.average_sas = self._get_average_sas()
        self.total_better_scored_paired_sessions = (
            self._get_total_better_scored_paired_sessions()
        )

    def _get_zone_difficulty_level(self, _date):
        zone_difficulty_level = ZoneDifficultyLevel.objects.filter(
            user_auth=self.user_auth, created_at__date__lt=_date
        ).last()
        if zone_difficulty_level:
            return zone_difficulty_level.get_current_level(self.zone_focus)

    def _get_days_since_last_unpaired(self):
        planned_session_codes = list(
            ActualSession.objects.filter_actual_sessions(
                user_auth=self.user_auth,
                session_code__isnull=False,
                session_date_time__date__lt=self.user_local_date,
            ).values_list("session_code", flat=True)
        )

        # Last planned session that was not paired with any actual session
        last_unpaired_planned_session = (
            PlannedSession.objects.filter(
                user_auth=self.user_auth,
                session_date_time__date__lt=self.user_local_date,
            )
            .exclude(zone_focus=0)
            .exclude(session_code__in=planned_session_codes)
            .values("session_date_time")
            .last()
        )

        query_conditions = {
            "user_auth": self.user_auth,
            "is_active": True,
            "session_date_time__date__lte": self.end_date,
        }
        if last_unpaired_planned_session:
            last_unpaired_session_date = last_unpaired_planned_session[
                "session_date_time"
            ].date()
            query_conditions.update(
                {"session_date_time__date__gt": last_unpaired_session_date}
            )
        return (
            PlannedSession.objects.filter(**query_conditions)
            .exclude(zone_focus=0)
            .count()
        )

    def _get_average_sas(self):
        average_sas = (
            ActualSession.objects.filter_actual_sessions(
                user_auth=self.user_auth,
                session_date_time__range=(self.start_date, self.end_date),
            )
            .aggregate(Avg("session_score__intensity_accuracy_score"))
            .get("session_score__intensity_accuracy_score__avg")
            or 0
        )
        return average_sas / 100

    def _get_total_better_scored_paired_sessions(self):
        return self.actual_sessions.filter(
            session_code__isnull=False, session_score__sas_today_score__gt=70
        ).count()

    def _get_this_week_remarks(self):
        if not self.planned_sessions.exists():
            return []

        if self.zone_focus == 0:
            return self._get_recovery_zone_current_week_remarks()
        return self._get_build_zone_current_week_remarks()

    def _get_recovery_zone_current_week_remarks(self):
        planned_pss = self.planned_sessions.aggregate(Sum("planned_pss")).get(
            "planned_pss__sum"
        )
        actual_pss = self.actual_sessions.aggregate(Sum("actual_pss")).get(
            "actual_pss__sum"
        )

        if actual_pss is not None and actual_pss > planned_pss * Decimal(1.1):
            return [WeekAnalysisWeekRemarks.PSS_RECOVERY.value]
        return [WeekAnalysisWeekRemarks.RECOVERY_WEEK.value]

    def _get_build_zone_current_week_remarks(self):
        if not self.actual_sessions.filter(session_code__isnull=False).exists():
            return [WeekAnalysisWeekRemarks.NO_PAIRED.value]

        if self.zone_focus == 1:
            self._get_zone1_current_week_remarks()

        current_week_remarks = [
            f"You managed to spend a total of "
            f"{convert_second_to_str(self.actual_time_in_zone)} training out of "
            f"{convert_second_to_str(self.planned_time_in_zone)} training the "
            f"{self.zone_description} system (this weeks focus).",
            f"You completed a total of {self.total_paired_sessions} out of "
            f"{self.total_planned_sessions}. Of which "
            f"{self.total_better_scored_paired_sessions or 0} followed the plan. Your "
            f"current streak of completed sessions is: "
            f"{self.days_since_last_unpaired} day{'s' if self.days_since_last_unpaired > 1 else ''}.",
        ]
        if (
            self.starting_zone_difficulty_level == 0
            and self.ending_zone_difficulty_level > 0
        ):
            current_week_remarks.append(WeekAnalysisWeekRemarks.ACHIEVEMENT.value)
        if (
            self.starting_zone_difficulty_level is not None
            and self.ending_zone_difficulty_level > self.starting_zone_difficulty_level
        ):
            current_week_remarks.append(
                WeekAnalysisWeekRemarks.ZONE_DIFFICULTY_LEVEL.value
            )
        if self.actual_time_in_zone > self.planned_time_in_zone * 0.8:
            current_week_remarks.append(
                WeekAnalysisWeekRemarks.TIME_IN_ZONE.value.format(
                    zone_focus=self.zone_focus
                )
            )
        if self.average_sas > 70:
            current_week_remarks.append(WeekAnalysisWeekRemarks.SAS.value)
        return current_week_remarks

    def _get_zone1_current_week_remarks(self):
        planned_duration = self.planned_sessions.aggregate(Sum("planned_duration")).get(
            "planned_duration__sum"
        )
        actual_duration = self.actual_sessions.aggregate(Sum("actual_duration")).get(
            "actual_duration__sum"
        )

        current_week_remarks = []
        if actual_duration > planned_duration * Decimal(1.1):
            current_week_remarks.append(WeekAnalysisWeekRemarks.PSS_ZONE1.value)
        else:
            planned_pss = self.planned_sessions.aggregate(Sum("planned_pss")).get(
                "planned_pss__sum"
            )
            actual_pss = self.actual_sessions.aggregate(Sum("actual_pss")).get(
                "actual_pss__sum"
            )
            if Decimal(0.25) * planned_pss < actual_pss < Decimal(0.75) * planned_pss:
                current_week_remarks.append(
                    "Well done for getting some riding completed this week. This will all help to the body switched on again"
                )
            elif actual_pss >= Decimal(0.75) * planned_pss:
                current_week_remarks.append("A great week of training!")
            else:
                current_week_remarks.append(
                    "Looks like you were not able to complete as much riding as planned. Please let us know via the feedback if there are any problems."
                )

    def _get_last_week_comparison_remarks(self):
        if self.previous_week_analysis is None or self.zone_focus == 0:
            return []

        comparison_texts = []

        if self.zone_focus == 1:
            if self.duration > self.previous_week_analysis.duration:
                comparison_texts.append(
                    WeekAnalysisWeekRemarks.DURATION_COMPARISON.value.format(
                        duration=self.duration,
                        previous_week_duration=self.previous_week_analysis.duration,
                    )
                )
            return comparison_texts

        if self.actual_time_in_zone > self.previous_week_analysis.actual_time_in_zone:
            time_difference = (
                self.actual_time_in_zone
                - self.previous_week_analysis.actual_time_in_zone
            )
            comparison_texts.append(
                WeekAnalysisWeekRemarks.TIME_DIFFERENCE_COMPARISON.value.format(
                    time_difference=convert_second_to_str(time_difference)
                )
            )
        if self.average_sas > self.previous_week_analysis.average_sas:
            comparison_texts.append(WeekAnalysisWeekRemarks.SAS_COMPARISON.value)
        if (
            self.zone_focus != 7
            and self.actual_time_above_zone
            < self.previous_week_analysis.actual_time_above_zone
            and self.planned_time_in_zone
            < self.previous_week_analysis.actual_time_in_zone
        ):
            comparison_texts.append(
                WeekAnalysisWeekRemarks.TIME_IN_ZONE_COMPARISON.value.format(
                    zone_focus=self.zone_focus
                )
            )
        return comparison_texts

    def _get_tips_for_next_week(self):
        if self.zone_focus in (0, 1):
            return []

        tips_texts = []
        if Decimal(self.average_sas) < Decimal(0.7):
            tips_texts.append(
                WeekAnalysisWeekRemarks.SAS_TIPS.value.format(
                    zone_description=self.zone_description
                )
            )
        if (
            self.zone_focus != 7
            and self.actual_time_above_zone > 1.15 * self.planned_time_above_zone
        ):
            tips_texts.append(
                WeekAnalysisWeekRemarks.TIME_ABOVE_ZONE_TIPS.value.format(
                    actual_time_above_zone=self.actual_time_above_zone,
                    zone_focus=self.zone_focus,
                )
            )
        if self.planned_time_in_zone > self.actual_time_above_zone * 0.85:
            tips_texts.append(
                WeekAnalysisWeekRemarks.TIME_IN_ZONE_TIPS.value.format(
                    zone_focus=self.zone_focus
                )
            )
        if self.zone_focus == 7:
            athlete_activity_codes = list(
                self.actual_sessions.filter(
                    athlete_activity_code__isnull=False,
                ).values_list("athlete_activity_code", flat=True)
            )

            max_cadence = 0
            for athlete_activity_code in athlete_activity_codes:
                athlete_activity = dakghor_get_athlete_activity(
                    athlete_activity_code
                ).json()["data"]["athlete_activity"]
                cadence = get_max_cadence_from_ride_summary(
                    athlete_activity["ride_summary"]
                )
                if cadence is not None and cadence > max_cadence:
                    max_cadence = cadence

            if 0 < max_cadence < 110:
                tips_texts.append(WeekAnalysisWeekRemarks.CADENCE_TIPS.value)

        return tips_texts

    def _get_planned_sessions_codes(self):
        return list(
            PlannedSession.objects.filter(
                user_auth=self.user_auth,
                is_active=True,
                session_date_time__date__range=(self.start_date, self.end_date),
            ).values_list("session_code", flat=True)
        )


class WeekAnalysisUTPRemarks:
    def __init__(self, user_auth, user_local_date):
        self.user_auth = user_auth
        self.start_date = user_local_date
        self.end_date = user_local_date + timedelta(6)
        self.user_local_date = user_local_date

        self.has_utp_updated_sessions = False
        self.reasons_texts = []

    def generate_utp_remarks(self):
        if not self._is_utp_run_for_user():
            empty_dict = {"title": "", "remarks": []}
            return {
                "utp_summary": empty_dict,
                "utp_reason": empty_dict,
            }

        return {
            "utp_summary": self._get_utp_summary(),
            "utp_reason": self._get_utp_reasons(),
        }

    def _is_utp_run_for_user(self):
        cron_code = CronHistoryLog.CronCode.AUTO_UPDATE_TRAINING_PLAN.value
        last_utp = (
            CronHistoryLog.objects.filter(cron_code=cron_code, user_auth=self.user_auth)
            .values("timestamp")
            .last()
        )
        if not last_utp:
            return False

        last_utp_timestamp = last_utp["timestamp"]
        hour_difference = (
            datetime.datetime.now() - last_utp_timestamp.replace(tzinfo=None)
        ).total_seconds() // 3600

        # 30 hour difference was not a requirement. It was added so that we can have
        # a window of time even if some error occurs.
        return bool(hour_difference <= 30)

    def _get_utp_summary(self):
        old_planned_sessions = (
            PlannedSession.objects.filter(
                user_auth=self.user_auth,
                is_active=False,
                session_date_time__date__range=(self.start_date, self.end_date),
            )
            .order_by("session_date_time", "-created_at")
            .distinct("session_date_time")
        )
        new_planned_sessions = PlannedSession.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            session_date_time__date__range=(self.start_date, self.end_date),
        )

        summary_texts = []
        for index, new_planned_session in enumerate(new_planned_sessions):
            old_planned_session = old_planned_sessions[index]

            summary_text = self._get_session_summary(
                new_planned_session.session_date_time.date(),
                old_planned_session,
                new_planned_session,
            )
            if summary_text:
                summary_texts.append(summary_text)

        if summary_texts:
            title = WeekAnalysisUTPSummary.TITLE.value
            remarks = summary_texts
        else:
            title = WeekAnalysisUTPSummary.NO_CHANGE.value
            remarks = []

        return {"title": title, "remarks": remarks}

    def _get_session_summary(self, session_date, old_session, new_session):
        summary_text = ""
        if old_session.name != new_session.name:
            summary_text += (
                f"{session_date} : {old_session.name} changed to {new_session.name}."
            )
        else:
            if old_session.planned_duration != new_session.planned_duration:
                summary_text += self._get_change_text(
                    old_session.planned_duration, new_session.planned_duration
                )
                summary_text += (
                    f" {session_date} : {old_session.planned_duration} "
                    f"changed to {new_session.planned_duration}. "
                )
            if old_session.planned_intensity != new_session.planned_intensity:
                summary_text += self._get_change_text(
                    old_session.planned_intensity, new_session.planned_intensity
                )
                summary_text += (
                    f" {session_date} : {old_session.planned_duration} "
                    f"changed to {new_session.planned_duration}."
                )
        return summary_text

    @staticmethod
    def _get_change_text(old_data, new_data):
        return "Increased" if new_data > old_data else "Decreased"

    def _get_utp_reasons(self):
        if not self.has_utp_updated_sessions:
            self.reasons_texts = []
        else:
            self._set_first_and_third_reason()
            self._set_second_reason()

        if self.reasons_texts:
            title = WeekAnalysisUTPSummary.TITLE.value
            remarks = self.reasons_texts
        else:
            title = None
            remarks = []

        return {"title": title, "remarks": remarks}

    def _set_first_and_third_reason(self):
        actual_freshness = ActualDay.objects.get_actual_freshness(
            user_auth=self.user_auth,
            activity_date=self.user_local_date,
        )
        planned_freshness = PlannedDay.objects.get_planned_freshness(
            self.user_auth, activity_date=self.user_local_date
        )

        next_week_old_pss = self._get_planned_sessions_pss(is_active=False)
        next_week_new_pss = self._get_planned_sessions_pss(is_active=True)

        if (
            actual_freshness < planned_freshness
            and next_week_new_pss < next_week_old_pss
        ):
            self.reasons_texts.append(WeekAnalysisUTPReason.FIRST_REASON.value)

        if (
            next_week_new_pss > next_week_old_pss
            and actual_freshness > planned_freshness
        ):
            self.reasons_texts.append(WeekAnalysisUTPReason.THIRD_REASON.value)

    def _get_planned_sessions_pss(self, is_active: bool):
        return (
            PlannedSession.objects.filter(
                user_auth=self.user_auth,
                is_active=is_active,
                session_date_time__date__range=(self.start_date, self.end_date),
            )
            .order_by(
                "-session_date_time",
            )
            .distinct("session_date_time__date")
            .aggregate(Sum("planned_pss"))
        )["planned_pss__sum"]

    def _set_second_reason(self):
        actual_session_count = ActualSession.objects.filter_actual_sessions(
            user_auth=self.user_auth,
            session_code__in=self._get_planned_sessions_codes(),
        ).count()
        planned_session_count = PlannedSession.objects.filter_zone_difficulty_sessions(
            user_auth=self.user_auth,
            is_active=True,
            session_date_time__date__range=(self.start_date, self.end_date),
        ).count()

        if actual_session_count < planned_session_count:
            old_next_week_zone_focus = self._get_next_week_zone_focus(is_active=False)
            new_next_week_zone_focus = self._get_next_week_zone_focus(is_active=True)

            if old_next_week_zone_focus != new_next_week_zone_focus:
                self.reasons_texts.append(WeekAnalysisUTPReason.SECOND_REASON.value)

    def _get_planned_sessions_codes(self):
        return list(
            PlannedSession.objects.filter_zone_difficulty_sessions(
                user_auth=self.user_auth,
                is_active=True,
                session_date_time__date__range=(self.start_date, self.end_date),
            ).values_list("session_code", flat=True)
        )

    def _get_next_week_zone_focus(self, is_active: bool):
        user_week = (
            UserWeek.objects.filter(
                user_auth=self.user_auth,
                is_active=is_active,
                start_date__range=(self.start_date, self.end_date),
            )
            .values("zone_focus")
            .last()
        )
        return user_week.get("zone_focus") if user_week else None


class GenerateWeekAnalysis:
    def __init__(self, user_auth: UserAuthModel, user_local_date: date):
        self.user_auth = user_auth
        self.user_local_date = user_local_date
        self.end_date = self.user_local_date - timedelta(1)
        self.start_date = self.end_date - timedelta(days=6)
        self.user_week = self._get_user_week()

        self.extra_log_fields = log_extra_fields(
            user_auth_id=user_auth.id,
            user_id=user_auth.code,
            service_type=ServiceType.INTERNAL.value,
        )

        self.week_analysis_context = {
            "user_id": self.user_auth.code,
            "code": uuid.uuid4(),
            "report_date": self.user_local_date,
            "week_start_date": self.start_date,
            "week_end_date": self.end_date,
        }

        self.zone_focus = None
        self.zone_description = None
        self.is_ftp_available = False
        self.is_fthr_available = False

        self.actual_sessions = ActualSession.objects.filter_actual_sessions(
            user_auth=self.user_auth,
            activity_type=ActivityTypeEnum.CYCLING.value[1],
            session_date_time__date__range=(self.start_date, self.end_date),
        )

    def _get_user_week(self):
        return (
            UserWeek.objects.filter(
                user_auth=self.user_auth,
                is_active=True,
                start_date__range=(self.start_date, self.end_date),
            )
            .values("zone_focus", "block_code", "week_code")
            .last()
        )

    def generate_report(self):
        logger.info("Generating week analysis", extra=self.extra_log_fields)

        self._set_week_info()
        self._set_basic_stats()
        self._set_actual_time_in_zones()
        self._set_planned_time_in_zones()
        self._set_ftp_fthr_availability()
        self._set_utp_remarks()
        self._set_week_remarks()

        return WeekAnalysis.objects.create(**self.week_analysis_context)

    def _set_week_info(self):
        week_no = self._get_week_no()
        total_weeks_in_block = self._get_total_weeks_in_block()
        week_title = self._get_week_title(week_no, total_weeks_in_block)
        self.week_analysis_context.update(
            {
                "week_no": week_no,
                "total_weeks_in_block": total_weeks_in_block,
                "week_title": week_title,
            }
        )

    def _get_week_no(self):
        if not self.user_week:
            return

        user_weeks_under_block = list(
            UserWeek.objects.filter(
                block_code=self.user_week["block_code"], is_active=True
            )
            .order_by("start_date")
            .values_list("week_code", flat=True)
        )
        return user_weeks_under_block.index(self.user_week["week_code"]) + 1

    def _get_total_weeks_in_block(self):
        if not self.user_week:
            return

        user_block = (
            UserBlock.objects.filter(
                block_code=self.user_week["block_code"], is_active=True
            )
            .values("no_of_weeks")
            .last()
        )
        if user_block:
            return user_block["no_of_weeks"]

    def _get_week_title(self, week_no, total_weeks_in_block):
        self.zone_description = self._get_zone_description()
        return WeekAnalysisReportTitle.get_week_title(
            week_no=week_no,
            total_weeks_in_block=total_weeks_in_block,
            zone_description=self.zone_description,
        )

    def _get_zone_description(self):
        self.zone_focus = self.user_week.get("zone_focus") if self.user_week else None

        if self.zone_focus is not None:
            return WeekAnalysisZoneDescription.get_zone_description(self.zone_focus)

    def _set_basic_stats(self):
        basic_stats = self.actual_sessions.aggregate(
            Sum("actual_distance_in_meters"),
            Sum("actual_duration"),
            Sum("elevation_gain"),
            Sum("actual_pss"),
            Count("id"),
        )

        self.week_analysis_context.update(
            {
                "distance": basic_stats["actual_distance_in_meters__sum"] or 0,
                "duration": basic_stats["actual_duration__sum"] or 0,
                "elevation": basic_stats["elevation_gain__sum"] or 0,
                "total_rides": basic_stats["id__count"] or 0,
                "pss": basic_stats["actual_pss__sum"] or 0,
            }
        )

    def _set_actual_time_in_zones(self):
        logger.info("Fetching actual time in zone data", extra=self.extra_log_fields)

        athlete_activity_codes = list(
            self.actual_sessions.filter(
                athlete_activity_code__isnull=False,
            ).values_list("athlete_activity_code", flat=True)
        )

        logger.info(
            "Fetching time in zone data from Dakghor", extra=self.extra_log_fields
        )
        actual_sessions = dakghor_get_time_in_zones(athlete_activity_codes)

        actual_time_in_power_zones = initialize_dict(0, 8)
        actual_time_in_hr_zones = initialize_dict(0, 7)
        for actual_session in actual_sessions:
            time_in_power_zone = eval(actual_session["time_in_power_zone"])
            time_in_hr_zone = eval(actual_session["time_in_heart_rate_zone"])

            actual_time_in_power_zones = add_time_in_zones(
                actual_time_in_power_zones, time_in_power_zone
            )
            actual_time_in_hr_zones = add_time_in_zones(
                actual_time_in_hr_zones, time_in_hr_zone
            )

        self.week_analysis_context.update(
            {
                "actual_time_in_power_zones": actual_time_in_power_zones,
                "actual_time_in_hr_zones": actual_time_in_hr_zones,
            }
        )

    def _set_planned_time_in_zones(self):
        logger.info("Fetching planned time in zone data", extra=self.extra_log_fields)
        planned_sessions = PlannedSession.objects.filter(
            user_auth=self.user_auth,
            is_active=True,
            session_date_time__date__range=(self.start_date, self.end_date),
        ).values(
            "session_date_time", "planned_time_in_power_zone", "planned_time_in_hr_zone"
        )

        planned_time_in_power_zones = initialize_dict(0, 8)
        planned_time_in_hr_zones = initialize_dict(0, 7)
        for planned_session in planned_sessions:
            time_in_power_zone = eval(planned_session["planned_time_in_power_zone"])
            time_in_hr_zone = eval(planned_session["planned_time_in_hr_zone"])

            planned_time_in_power_zones = add_time_in_zones(
                planned_time_in_power_zones, time_in_power_zone
            )
            planned_time_in_hr_zones = add_time_in_zones(
                planned_time_in_hr_zones, time_in_hr_zone
            )

        self.week_analysis_context.update(
            {
                "planned_time_in_power_zones": planned_time_in_power_zones,
                "planned_time_in_hr_zones": planned_time_in_hr_zones,
            }
        )

    def _set_ftp_fthr_availability(self):
        user_personalise_data = UserPersonaliseData.objects.filter(
            user_auth=self.user_auth, is_active=True
        ).last()
        self.is_ftp_available = bool(user_personalise_data.current_ftp) and (
            is_time_spent_in_zone(
                self.week_analysis_context["planned_time_in_power_zones"]
            )
            or is_time_spent_in_zone(
                self.week_analysis_context["actual_time_in_power_zones"]
            )
        )
        self.is_fthr_available = bool(user_personalise_data.current_fthr) and (
            is_time_spent_in_zone(
                self.week_analysis_context["planned_time_in_hr_zones"]
            )
            or is_time_spent_in_zone(
                self.week_analysis_context["actual_time_in_hr_zones"]
            )
        )

        self.week_analysis_context.update(
            {
                "is_ftp_available": self.is_ftp_available,
                "is_fthr_available": self.is_fthr_available,
            }
        )

    def _set_utp_remarks(self):
        utp_remarks = WeekAnalysisUTPRemarks(
            self.user_auth, self.user_local_date
        ).generate_utp_remarks()
        self.week_analysis_context.update(utp_remarks)

    def _set_week_remarks(self):

        if self.is_ftp_available:
            actual_time_in_zones = self.week_analysis_context[
                "actual_time_in_power_zones"
            ]
            planned_time_in_zones = self.week_analysis_context[
                "planned_time_in_power_zones"
            ]
        else:
            actual_time_in_zones = self.week_analysis_context["actual_time_in_hr_zones"]
            planned_time_in_zones = self.week_analysis_context[
                "planned_time_in_hr_zones"
            ]

        week_remarks = WeekAnalysisRemarks(
            user_auth=self.user_auth,
            user_local_date=self.user_local_date,
            start_date=self.start_date,
            end_date=self.end_date,
            zone_focus=self.zone_focus,
            zone_description=self.zone_description,
            actual_sessions=self.actual_sessions,
            duration=self.week_analysis_context["duration"],
            total_rides=self.week_analysis_context["total_rides"],
            actual_time_in_zones=actual_time_in_zones,
            planned_time_in_zones=planned_time_in_zones,
        ).get_remarks()

        self.week_analysis_context.update(week_remarks)
