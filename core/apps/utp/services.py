import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction

from core.apps.block.models import UserBlock
from core.apps.calculations.onboarding.ramp_rate_calculations import (
    get_calculated_ramp_rate,
)
from core.apps.common.common_functions import (
    clear_user_cache,
    get_auto_update_start_date,
)
from core.apps.common.const import (
    MAX_TYPICAL_INTENSITY,
    MIN_AVAILABLE_TRAINING_HOUR,
    MIN_STARTING_LOAD,
    PSS_SL_MIN,
)
from core.apps.common.date_time_utils import DateTimeUtils, daterange
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import log_extra_fields, update_is_active_value
from core.apps.ctp.calculations import (
    PssCalculation,
    calculate_target_load,
    create_session_for_day,
    final_load_calculation_for_day,
    get_commute_pss_for_week,
    get_minimum_pss,
    get_number_of_sessions_of_this_type_in_this_week,
    get_number_of_week_days,
    get_session_types_for_this_week,
    get_yesterdays_session_intensity,
    is_pad_applicable,
    select_session,
)
from core.apps.ctp.services import TrainingAvailability, ZoneDifficultyService
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.session.cached_truth_tables_utils import (
    get_rest_session,
    get_session_rule_by_session_type,
    get_session_type_by_session,
)
from core.apps.session.models import PlannedSession
from core.apps.week.models import UserWeek

logger = logging.getLogger(__name__)


class UpdateTrainingPlan:
    def __init__(
        self,
        user_auth,
        user_weeks_to_update=None,
        auto_update_start_date=None,
        is_utp=True,
    ):
        self.user_auth = user_auth

        self.auto_update_start_date = (
            auto_update_start_date or self._get_auto_update_start_date()
        )
        self.weeks_to_update = (
            user_weeks_to_update
            or UserWeek.objects.filter(
                user_block__user_auth=self.user_auth,
                start_date__gte=self.auto_update_start_date,
                is_active=True,
            ).order_by("start_date")[:4]
        )
        self.is_utp = is_utp

        self.user_plan = self.user_auth.user_plans.filter(
            is_active=True, end_date__gte=datetime.today()
        ).last()
        self.user_event = self.user_auth.user_events.filter(is_active=True).last()
        self.event_dates = self._get_user_event_dates()

        self.user_personalise_data = self.user_auth.personalise_data.filter(
            is_active=True
        ).last()
        self.training_availability_object = TrainingAvailability(self.user_auth)
        self.zone_difficulty_service = ZoneDifficultyService(
            self.user_auth, self.user_personalise_data
        )

        self.BLOCKS = []
        self.WEEKS = []
        self.DAYS = []
        self.SESSIONS = []

        self.BLOCK_NO = 0
        self.WEEK_NO = 0
        self.DAY_NO = 0
        self.SESSION_NO = 0

        self.current_week = None
        self.current_day = None

    def _get_user_event_dates(self):
        """Returns list of dates under which the event will occur"""
        start_date = self.user_event.start_date
        end_date = self.user_event.end_date
        return [event_date for event_date in daterange(start_date, end_date)]

    def _get_auto_update_start_date(self):
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            self.user_auth.timezone_offset, datetime.now()
        )
        return get_auto_update_start_date(user_local_date)

    def get_last_sunday_load(self):
        week = self.WEEKS[-1]
        return week.sunday_max_load

    def get_yesterday(self, day):
        if len(self.DAYS) > 0:
            return self.DAYS[-1]
        yesterday_date = day.activity_date - timedelta(days=1)
        # TODO Refactor with in memory query
        yesterday = PlannedDay.objects.filter(
            user_auth=self.user_auth, activity_date=yesterday_date, is_active=True
        ).last()
        if yesterday:
            yesterday.selected_session = PlannedSession.objects.filter(
                user_auth=self.user_auth, session_date_time=yesterday.activity_date
            ).last()
        return yesterday

    def user_had_session_for_last_three_days(self):
        if len(self.DAYS) < 3:
            return False
        d1_session = self.DAYS[-1].selected_session
        d2_session = self.DAYS[-2].selected_session
        d3_session = self.DAYS[-3].selected_session

        session_type_codes = [
            d1_session.session_type.code,
            d2_session.session_type.code,
            d3_session.session_type.code,
        ]
        return not bool("REST" in session_type_codes)

    def create_week(
        self,
        week_start_date,
        week_end_date,
        block,
        zone_focus,
        week_type,
        starting_week,
    ):
        try:
            week = UserWeek(
                user_auth=self.user_auth,
                start_date=week_start_date,
                end_date=week_end_date,
                user_block=block,
                week_type=week_type,
                user_id=self.user_auth.code,
                zone_focus=zone_focus,
                week_code=uuid.uuid4(),
                block_code=block.block_code,
            )
            if week_type == "RECOVERY":
                week_ramp_rate = -2
            else:
                week_ramp_rate = 2.5

            if week.start_date <= self.auto_update_start_date:
                yesterday_date = self.auto_update_start_date - timedelta(days=1)
                query_conditions = {
                    "user_auth": self.user_auth,
                    "activity_date": yesterday_date,
                    "is_active": True,
                }
                if self.is_utp:
                    previous_actual_day = (
                        ActualDay.objects.filter(**query_conditions)
                        .values("actual_load")
                        .last()
                    )
                    previous_day_load = (
                        previous_actual_day.get("actual_load")
                        if previous_actual_day
                        else None
                    )
                else:
                    previous_planned_day = (
                        PlannedDay.objects.filter(**query_conditions)
                        .values("planned_load")
                        .last()
                    )
                    previous_day_load = (
                        previous_planned_day.get("planned_load")
                        if previous_planned_day
                        else None
                    )

                if previous_day_load is None:
                    previous_day_load = self.user_personalise_data.starting_load
                starting_load = max(MIN_STARTING_LOAD, previous_day_load)

                target_ramp_calculation_date = self.auto_update_start_date
            elif starting_week:
                target_ramp_calculation_date = self.user_plan.start_date
                starting_load = self.user_personalise_data.starting_load
            else:
                target_ramp_calculation_date = week.start_date
                starting_load = self.WEEKS[-1].sunday_max_load
            ramp_rate = get_calculated_ramp_rate(
                target_ramp_calculation_date, week_ramp_rate
            )
            week.sunday_max_load = starting_load + Decimal.from_float(ramp_rate)
            week_commute_pss = get_commute_pss_for_week(
                self.training_availability_object
            )
            week.commute_pss_week = (
                week_commute_pss  # this is a constant value refactor this
            )

            self.WEEK_NO += 1
            week.temp_week_no = self.WEEK_NO
            if not block.pk:
                week.temp_block_no = block.temp_user_block_no

            # create days of this week
            self.create_week_days(week)
            week.sunday_max_load = self.DAYS[-1].planned_load

            self.WEEKS.append(week)

        except Exception as e:
            week = None
            logger.exception(
                "Failed to create week in update training plan",
                extra=log_extra_fields(
                    user_auth_id=self.user_auth.id,
                    exception_message=str(e),
                    service_type=ServiceType.INTERNAL.value,
                ),
            )
        return week

    def create_week_days(self, week):
        _date = week.end_date
        target_load = week.sunday_max_load

        week_days = []
        number_of_week_days = get_number_of_week_days(week)
        for _ in range(number_of_week_days):
            if _date < self.auto_update_start_date:
                continue

            day = PlannedDay(
                user_auth=self.user_auth,
                activity_date=_date,
                max_load=target_load,
                week_code=week.week_code,
                day_code=uuid.uuid4(),
                user_id=self.user_auth.code,
            )

            _date = day.activity_date - timedelta(days=1)
            day.temp_week_no = self.WEEK_NO
            week_days.append(day)

            target_load = calculate_target_load(day.max_load)

        days_with_session, sessions = self.select_sessions_for_week_days(
            week, week_days[::-1]
        )
        self.SESSIONS += sessions
        return days_with_session

    def check_rest_day(self, day, available_training_hour):
        return (
            self.user_had_session_for_last_three_days()
            or available_training_hour < MIN_AVAILABLE_TRAINING_HOUR
            or get_minimum_pss(day) < PSS_SL_MIN
            or day.activity_date in self.event_dates
        )

    def _set_as_rest_day(self, day, utp, actual_yesterday, auto_update_start_date=None):
        rest_session = get_rest_session()
        session_type = get_session_type_by_session(rest_session)
        session = create_session_for_day(
            rest_session, session_type, day, None, padding=False
        )
        day = final_load_calculation_for_day(
            self.user_plan,
            day,
            session,
            actual_yesterday,
            self.user_personalise_data,
            utp,
            auto_update_start_date,
        )
        day.zone_focus = session.session_type.target_zone
        session.session = rest_session
        day.selected_session = session
        return day, session

    def select_build_session(
        self, week, week_days, day, pss_calc, available_training_hour, actual_yesterday
    ):
        session_types = get_session_types_for_this_week(week)
        planned_session = None
        for session_type in session_types:
            if (
                get_session_rule_by_session_type(session_type).typical_intensity
                > MAX_TYPICAL_INTENSITY
                and get_yesterdays_session_intensity(
                    day, self.is_utp, self.auto_update_start_date
                )
                > MAX_TYPICAL_INTENSITY
            ):
                continue
            number_of_sessions_of_this_type_in_this_week = (
                get_number_of_sessions_of_this_type_in_this_week(
                    week_days, session_type
                )
            )
            if (
                number_of_sessions_of_this_type_in_this_week
                >= get_session_rule_by_session_type(
                    session_type
                ).max_num_of_selected_session_type_per_week
            ):
                continue

            # training pss hours available calculations 2.10
            day.training_pss_by_hours = pss_calc.get_training_pss_available_hours(
                session_type,
                day,
                self.training_availability_object.user_available_hours,
            )

            # training pss final values calculations 2.11
            minimum_of_training_pss_calculations = min(
                day.training_pss_by_load,
                day.training_pss_by_freshness,
                day.training_pss_by_max_ride,
                day.training_pss_by_hours,
            )
            day.training_pss_final_value = minimum_of_training_pss_calculations

            selected_session = select_session(
                day, session_type, self.zone_difficulty_service
            )
            self.zone_difficulty_service.update_zone_difficulty_level(selected_session)

            if selected_session:
                padding = is_pad_applicable(day, selected_session)
                day.zone_focus = selected_session.session_type.target_zone
                planned_session = create_session_for_day(
                    selected_session=selected_session,
                    session_type=session_type,
                    day=day,
                    available_training_hour=available_training_hour,
                    padding=padding,
                )
                planned_session.session = selected_session
                day = final_load_calculation_for_day(
                    self.user_plan,
                    day,
                    planned_session,
                    actual_yesterday,
                    self.user_personalise_data,
                    utp=self.is_utp,
                    auto_update_start_date=self.auto_update_start_date,
                )
                break
        return day, planned_session

    def select_sessions_for_week_days(self, week, days):
        week_days = []
        selected_sessions = []
        try:
            for day in days:
                if day.activity_date < self.user_plan.start_date:
                    continue

                yesterday = self.get_yesterday(day)
                day.yesterday = yesterday
                actual_yesterday = None
                if yesterday:
                    actual_yesterday = ActualDay.objects.filter(
                        activity_date=yesterday.activity_date,
                        is_active=True,
                        user_auth=self.user_auth,
                    ).last()
                pss_calc = PssCalculation(
                    self.user_personalise_data, week, utp=self.is_utp
                )

                # commute pss calculation 2.1
                day.commute_pss_day = pss_calc.get_commute_pss_of_day(
                    day, self.training_availability_object.commute_days
                )

                # load and acute load calculation 2.4
                (
                    load_post_commute_nth_day,
                    acute_load_post_commute_nth_day,
                ) = pss_calc.get_load_and_acute_load_post_commute_nth_day(
                    day, actual_yesterday
                )
                day.load_post_commute = load_post_commute_nth_day
                day.acute_load_post_commute = acute_load_post_commute_nth_day

                # training pss load calculations 2.5
                day.training_pss_by_load = pss_calc.get_training_pss_load(
                    day, actual_yesterday
                )

                # training pss freshness calculations 2.6
                day.training_pss_by_freshness = pss_calc.get_training_pss_freshness(
                    day, actual_yesterday
                )

                # training pss max ride calculations 2.7
                day.training_pss_by_max_ride = pss_calc.get_training_pss_max_ride(
                    day, actual_yesterday
                )

                available_training_hour = self.training_availability_object.get_available_training_hour_for_day(
                    day.activity_date
                )

                if self.check_rest_day(day, available_training_hour):
                    day, session = self._set_as_rest_day(
                        day, self.is_utp, actual_yesterday, self.auto_update_start_date
                    )
                else:
                    day, session = self.select_build_session(
                        week,
                        week_days,
                        day,
                        pss_calc,
                        available_training_hour,
                        actual_yesterday,
                    )

                self.DAY_NO += 1
                day.temp_day_no = self.DAY_NO
                session.temp_day_no = day.temp_day_no
                selected_sessions.append(session)

                week.planned_pss = Decimal(week.planned_pss) + session.planned_pss
                day.selected_session = session
                week_days.append(day)
                self.DAYS.append(day)

        except Exception as e:
            logger.exception(
                "Failed to update training plan.",
                extra=log_extra_fields(
                    user_auth_id=self.user_auth.id,
                    exception_message=str(e),
                    service_type=ServiceType.INTERNAL.value,
                ),
            )
        return week_days, selected_sessions

    @transaction.atomic
    def run_auto_update_for_weeks(self):
        logger.info(
            "Updating user plan for user event",
            extra=log_extra_fields(
                user_auth_id=self.user_auth.id,
                user_id=self.user_auth.code,
                service_type=ServiceType.INTERNAL.value,
            ),
        )
        backup_days = None
        backup_sessions = None
        for week in self.weeks_to_update:
            update_is_active_value([week], False)

            planned_days_query_conditions = {
                "week_code": week.week_code,
                "is_active": True,
            }
            planned_sessions_query_conditions = {
                "session_date_time__date__range": (week.start_date, week.end_date),
                "is_active": True,
            }
            if week.start_date <= self.auto_update_start_date <= week.end_date:
                backup_days = PlannedDay.objects.filter(
                    activity_date__lt=self.auto_update_start_date,
                    week_code=week.week_code,
                    is_active=True,
                )
                backup_sessions = self.user_auth.planned_sessions.filter(
                    session_date_time__gte=week.start_date,
                    session_date_time__lt=self.auto_update_start_date,
                    is_active=True,
                )

                planned_days_query_conditions.update(
                    {"activity_date__gte": self.auto_update_start_date}
                )
                planned_sessions_query_conditions["session_date_time__date__range"] = (
                    self.auto_update_start_date,
                    week.end_date,
                )

            planned_days = PlannedDay.objects.filter(**planned_days_query_conditions)
            planned_sessions = self.user_auth.planned_sessions.filter(
                **planned_sessions_query_conditions
            )
            update_is_active_value(planned_days, False)
            update_is_active_value(planned_sessions, False)

            user_block = UserBlock.objects.get(
                block_code=week.block_code, is_active=True
            )
            starting_week = (
                self.user_plan.created_at.date() == self.auto_update_start_date
            )
            new_week = self.create_week(
                week.start_date,
                week.end_date,
                user_block,
                week.zone_focus,
                week.week_type,
                starting_week,
            )

            if backup_days and backup_sessions:
                backup_pss = 0
                for backup_day in backup_days:
                    backup_session = backup_sessions.filter(
                        session_date_time=backup_day.activity_date
                    ).last()
                    backup_session.day_code = backup_day.day_code
                    backup_session.save()
                    backup_pss += backup_sessions[0].planned_pss
                    backup_day.week_code = new_week.week_code
                    backup_day.save()
                new_week.planned_pss += backup_pss

                logger.info("Resetting backup days and sessions")
                backup_days = None
                backup_sessions = None

            user_blocks_updated_pss = (
                week.user_block.planned_pss
                - week.planned_pss
                + Decimal(new_week.planned_pss)
            )
            week.user_block.planned_pss = user_blocks_updated_pss
            week.user_block.save()

        weeks = self._save_updated_weeks()
        days = self._save_days(weeks)
        self._save_sessions(days)

        clear_user_cache(self.user_auth)

    def _save_updated_weeks(self):
        weeks = UserWeek.objects.bulk_create(self.WEEKS)
        return weeks

    def _save_days(self, weeks):
        for day in self.DAYS:
            week = weeks[day.temp_week_no - 1]
            day.user_week = week
        days = PlannedDay.objects.bulk_create(self.DAYS)
        return days

    def _save_sessions(self, days):
        for session in self.SESSIONS:
            day = days[session.temp_day_no - 1]
            session.planned_day = day
        sessions = PlannedSession.objects.bulk_create(self.SESSIONS)
        return sessions
