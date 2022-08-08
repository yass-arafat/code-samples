import abc
import calendar
import logging
import math
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Union

from core.apps.block.models import UserBlock
from core.apps.calculations.onboarding.ramp_rate_calculations import (
    get_calculated_ramp_rate,
)
from core.apps.common.common_functions import get_date_from_datetime
from core.apps.common.const import (
    BUILD_WEEK_RAMP_RATE,
    BUILD_WEEK_TYPE,
    MAX_TYPICAL_INTENSITY,
    MIN_AVAILABLE_TRAINING_HOUR,
    MIN_WEEKLY_PSS,
    PSS_SL_MIN,
    RECOVERY_WEEK_RAMP_RATE,
    RECOVERY_WEEK_TYPE,
    TOTAL_SESSIONS_NEEDED_TO_UPGRADE_ZONE_DIFFICULTY_LEVEL,
)
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.session.cached_truth_tables_utils import (
    get_rest_session,
    get_session_rule_by_session_type,
    get_session_type_by_session,
)
from core.apps.session.models import PlannedSession
from core.apps.user_profile.models import ZoneDifficultyLevel
from core.apps.week.models import UserWeek

from ..common.date_time_utils import daterange
from .calculations import (
    PssCalculation,
    calculate_target_load,
    create_session_for_day,
    final_load_calculation_for_day,
    get_commute_pss_for_week,
    get_first_block_start_date,
    get_minimum_pss,
    get_number_of_sessions_of_this_type_in_this_week,
    get_number_of_week_days,
    get_session_types_for_this_week,
    get_total_weeks,
    get_weeks_per_block,
    get_yesterdays_session_intensity,
    get_zone_focuses,
    is_pad_applicable,
    select_session,
)

calendar.setfirstweekday(calendar.MONDAY)
logger = logging.getLogger(__name__)


class TrainingAvailability:
    def __init__(self, user_auth, training_availability=None):
        if not training_availability:
            training_availability = user_auth.training_availabilities.last()

        self.commute_days = self._get_commute_days(
            training_availability.days_commute_by_bike
        )
        self.single_commute_duration_hours = (
            training_availability.duration_single_commute_in_hours
        )
        self.user_available_hours = self._get_user_available_training_hours(
            training_availability.available_training_hours_per_day_outside_commuting
        )

    @staticmethod
    def _get_commute_days(commute_week):
        commute_days_dict = commute_week.__dict__
        del commute_days_dict["_state"]
        del commute_days_dict["id"]
        del commute_days_dict["created_at"]
        del commute_days_dict["updated_at"]
        commute_days_list = [float(item) for key, item in commute_days_dict.items()]
        return commute_days_list

    @staticmethod
    def _get_user_available_training_hours(
        available_training_hours_per_day_outside_commuting,
    ):
        dict_of_user_available_hours_for_a_week = (
            available_training_hours_per_day_outside_commuting.__dict__
        )
        del dict_of_user_available_hours_for_a_week["_state"]
        del dict_of_user_available_hours_for_a_week["id"]
        del dict_of_user_available_hours_for_a_week["created_at"]
        del dict_of_user_available_hours_for_a_week["updated_at"]
        user_available_hours_list = [
            float(item) for key, item in dict_of_user_available_hours_for_a_week.items()
        ]
        return user_available_hours_list

    def get_available_training_hour_for_day(self, activity_date):
        return self.user_available_hours[activity_date.weekday()]


class ZoneDifficultyService:
    def __init__(self, user_auth, user_personalise_data):
        self.user_auth = user_auth
        self.user_personalise_data = user_personalise_data
        self.zone_difficulty_levels = self._initiate_zone_difficulty_levels()
        self._get_user_zone_difficulty_level()

    def _initiate_zone_difficulty_levels(self):
        difficulty_levels = {}
        for zone_no in range(8):  # Zone 0-7
            difficulty_levels.update(self._get_zone_level_dict(zone_no))

        # Zone HC
        difficulty_levels.update(self._get_zone_level_dict(zone_no="HC"))
        return difficulty_levels

    @staticmethod
    def _get_zone_level_dict(zone_no: Union[int, str]) -> dict:
        return {str(zone_no): {"level": 0, "sessions_assigned": 0}}

    def _get_user_zone_difficulty_level(self):
        try:
            user_zone_difficulty_level = ZoneDifficultyLevel.objects.get(
                user_auth=self.user_auth, is_active=True
            )
        except ZoneDifficultyLevel.DoesNotExist:
            raise ValueError("User must have active zone difficulty level")

        current_levels = user_zone_difficulty_level.get_current_levels()
        for zone_no, current_level in current_levels:
            self.zone_difficulty_levels[str(zone_no)]["level"] = current_level

    def _is_zone_upgradable(self, zone_no):
        # As the upgrade condition is same for all zones currently,
        # same conditions are used for all zones
        zone_no = str(zone_no)
        sessions_assigned = self.zone_difficulty_levels[zone_no]["sessions_assigned"]
        return (
            sessions_assigned >= TOTAL_SESSIONS_NEEDED_TO_UPGRADE_ZONE_DIFFICULTY_LEVEL
        )

    def update_zone_difficulty_level(self, selected_session):
        if selected_session is None or selected_session.difficulty_level is None:
            return

        zone_no = str(selected_session.session_type.get_zone_focus())
        if (
            selected_session.difficulty_level
            == self.zone_difficulty_levels[zone_no]["level"]
        ):
            self.zone_difficulty_levels[zone_no]["sessions_assigned"] += 1
            if self._is_zone_upgradable(zone_no):
                self.zone_difficulty_levels[zone_no]["level"] += 1
                self.zone_difficulty_levels[zone_no]["sessions_assigned"] = 0

    def is_session_difficulty_level_higher(self, zone_no, difficulty_level):
        zone_no = str(zone_no)
        return difficulty_level > self.zone_difficulty_levels[zone_no]["level"]


class BaseTrainingPlan:
    def __init__(
        self,
        user_auth,
        user_plan,
        user_event,
        user_training_availability,
        user_personalise_data=None,
    ):
        self.user_auth = user_auth
        self.user_plan = user_plan
        self.user_event = user_event
        self.event_dates = self._get_user_event_dates()

        self.user_personalise_data = (
            user_personalise_data
            or self.user_auth.personalise_data.filter(is_active=True).last()
        )
        self.training_availability = TrainingAvailability(
            self.user_auth, user_training_availability
        )
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

        self.current_week_allowable_pss = 0

    def _get_user_event_dates(self):
        """Returns list of dates under which the event will occur"""
        start_date = self.user_event.start_date
        end_date = self.user_event.end_date
        return [event_date for event_date in daterange(start_date, end_date)]

    @staticmethod
    def _get_week_ramp_rate(week_type):
        if week_type == RECOVERY_WEEK_TYPE:
            return RECOVERY_WEEK_RAMP_RATE
        return BUILD_WEEK_RAMP_RATE

    def _user_had_session_for_last_three_days(self):
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

    def _get_last_sunday_load(self):
        week = self.WEEKS[-1]
        return week.sunday_max_load

    def _get_yesterday(self, day):
        if len(self.DAYS) > 0:
            return self.DAYS[-1]

        day_yesterday = PlannedDay.objects.filter(
            user_auth=self.user_auth,
            activity_date=day.activity_date - timedelta(days=1),
            is_active=True,
        ).last()
        if day_yesterday:
            day_yesterday.selected_session = PlannedSession.objects.filter(
                user_auth=self.user_auth, session_date_time=day_yesterday.activity_date
            ).last()
        return day_yesterday

    def _check_rest_day(self, day, available_training_hour):
        return (
            self._user_had_session_for_last_three_days()
            or available_training_hour < MIN_AVAILABLE_TRAINING_HOUR
            or self._check_pss_for_build_session(day)
            or day.activity_date in self.event_dates
        )

    def _check_pss_for_build_session(self, day) -> bool:
        return max(get_minimum_pss(day), self.current_week_allowable_pss) < PSS_SL_MIN

    def _day_pss_calculation(self, day, actual_yesterday, pss_calc):
        # commute pss calculation 2.1
        day.commute_pss_day = pss_calc.get_commute_pss_of_day(
            day, self.training_availability.commute_days
        )

        # load and acute load calculation 2.4
        (
            load_post_commute_nth_day,
            acute_load_post_commute_nth_day,
        ) = pss_calc.get_load_and_acute_load_post_commute_nth_day(day, actual_yesterday)
        day.load_post_commute = load_post_commute_nth_day
        day.acute_load_post_commute = acute_load_post_commute_nth_day

        # training pss load calculations 2.5
        day.training_pss_by_load = pss_calc.get_training_pss_load(day, actual_yesterday)

        # training pss freshness calculations 2.6
        day.training_pss_by_freshness = pss_calc.get_training_pss_freshness(
            day, actual_yesterday
        )

        # training pss max ride calculations 2.7
        day.training_pss_by_max_ride = pss_calc.get_training_pss_max_ride(
            day, actual_yesterday
        )

    def _day_final_pss_value_calculation(self, day, session_type, pss_calc):
        # training pss hours available calculations 2.10
        day.training_pss_by_hours = pss_calc.get_training_pss_available_hours(
            session_type, day, self.training_availability.user_available_hours
        )

        # training pss final values calculations 2.11
        day.training_pss_final_value = self._get_available_pss_for_day(day)

    def _get_available_pss_for_day(self, day):
        return min(
            max(
                min(
                    day.training_pss_by_load,
                    day.training_pss_by_freshness,
                    day.training_pss_by_max_ride,
                ),
                self.current_week_allowable_pss,
            ),
            day.training_pss_by_hours,
        )

    def _select_sessions_for_week_days(self, week, days, pss_calc):
        week_days = []
        selected_sessions = []
        self.current_week_allowable_pss = MIN_WEEKLY_PSS

        for day in days:
            if day.activity_date < self.user_plan.start_date:
                continue

            yesterday = self._get_yesterday(day)
            day.yesterday = yesterday
            actual_yesterday = None
            if yesterday:
                actual_yesterday = ActualDay.objects.filter(
                    activity_date=yesterday.activity_date,
                    is_active=True,
                    user_auth=self.user_auth,
                ).last()
            self._day_pss_calculation(day, actual_yesterday, pss_calc)

            available_training_hour = (
                self.training_availability.get_available_training_hour_for_day(
                    day.activity_date
                )
            )

            if self._check_rest_day(day, available_training_hour):
                day, session = self._set_as_rest_day(day, actual_yesterday)
            else:
                day, session = self._select_build_session(
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

            day.selected_session = session
            week.planned_pss = Decimal(week.planned_pss) + session.planned_pss

            selected_sessions.append(session)
            week_days.append(day)
            self.DAYS.append(day)

            self.current_week_allowable_pss -= float(session.planned_pss)

        self.SESSIONS += selected_sessions

    @abc.abstractmethod
    def _set_as_rest_day(self, day, actual_yesterday):
        """Set day as a Recovery Day"""

    @abc.abstractmethod
    def _select_build_session(
        self, week, week_days, day, pss_calc, available_training_hour, actual_yesterday
    ):
        """Select training session for user"""

    def _create_week_days(self, week):
        _date = week.end_date
        target_load = week.sunday_max_load

        week_days = []
        number_of_week_days = get_number_of_week_days(week)
        for _ in range(number_of_week_days):
            day = PlannedDay(
                user_auth=self.user_auth,
                activity_date=_date,
                max_load=target_load,
                week_code=week.week_code,
                day_code=uuid.uuid4(),
            )

            _date = day.activity_date - timedelta(days=1)
            day.temp_week_no = self.WEEK_NO
            week_days.append(day)

            target_load = calculate_target_load(day.max_load)
        return week_days

    def _set_week_data(
        self,
        week,
        block,
        week_starting_load,
        target_ramp_calculation_date,
        week_ramp_rate,
    ):
        ramp_rate = get_calculated_ramp_rate(
            target_ramp_calculation_date, week_ramp_rate
        )
        week.sunday_max_load = week_starting_load + Decimal.from_float(ramp_rate)
        week_commute_pss = get_commute_pss_for_week(self.training_availability)
        week.commute_pss_week = (
            week_commute_pss  # this is a constant value refactor this
        )

        if not block.pk:
            week.temp_block_no = block.temp_user_block_no


class CreateTrainingPlan(BaseTrainingPlan):
    def __init__(
        self,
        user_auth,
        user_plan,
        user_event,
        user_training_availability,
        user_personalise_data=None,
    ):
        super().__init__(
            user_auth,
            user_plan,
            user_event,
            user_training_availability,
            user_personalise_data,
        )
        self.weeks_per_block = self._get_weeks_per_block()

    def _set_as_rest_day(self, day, actual_yesterday):
        rest_session = get_rest_session()
        session_type = get_session_type_by_session(rest_session)
        session = create_session_for_day(
            rest_session, session_type, day, None, padding=False
        )
        day = final_load_calculation_for_day(
            self.user_plan, day, session, actual_yesterday, self.user_personalise_data
        )
        day.zone_focus = session.session_type.target_zone
        session.session = rest_session
        day.selected_session = session
        return day, session

    def _select_build_session(
        self, week, week_days, day, pss_calc, available_training_hour, actual_yesterday
    ):
        session_types = get_session_types_for_this_week(week)
        session = None
        for session_type in session_types:
            if (
                get_session_rule_by_session_type(session_type).typical_intensity
                > MAX_TYPICAL_INTENSITY
                and get_yesterdays_session_intensity(day, utp=False)
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
            if self._check_recovery_week_intensive_session(
                week, session_type, day, week_days
            ):
                continue

            self._day_final_pss_value_calculation(day, session_type, pss_calc)

            selected_session = select_session(
                day, session_type, self.zone_difficulty_service
            )
            self.zone_difficulty_service.update_zone_difficulty_level(selected_session)

            if selected_session:
                padding = self._is_pad_applicable(week, day, selected_session)
                day.zone_focus = selected_session.session_type.target_zone
                session = create_session_for_day(
                    selected_session=selected_session,
                    session_type=session_type,
                    day=day,
                    available_training_hour=available_training_hour,
                    padding=padding,
                )
                session.session = selected_session
                day = final_load_calculation_for_day(
                    self.user_plan,
                    day,
                    session,
                    actual_yesterday,
                    self.user_personalise_data,
                    utp=False,
                )
                break
        return day, session

    def _check_recovery_week_intensive_session(
        self, week, session_type, day, week_days
    ):
        return bool(
            int(week.zone_focus) == 0
            and session_type.target_zone not in (0, 1)
            and (
                day.activity_date.weekday() in (0, 1)  # Monday, Tuesday
                or not self._is_build_session_assigned_this_week(week_days)
            )
        )

    @staticmethod
    def _is_pad_applicable(week, day, selected_session):
        if week.zone_focus == 0:
            return False
        return is_pad_applicable(day, selected_session)

    @staticmethod
    def _is_build_session_assigned_this_week(week_days):
        for day in week_days:
            if day.selected_session.zone_focus != 0:
                return True
        return False

    def _create_week(self, week_start_date, block, zone_focus, week_type):
        week_ramp_rate = self._get_week_ramp_rate(week_type)
        self.WEEK_NO += 1
        starting_week = self.WEEK_NO == 1
        if starting_week:
            target_ramp_calculation_date = self.user_plan.start_date
            starting_load = self.user_personalise_data.starting_load
        else:
            target_ramp_calculation_date = week_start_date
            starting_load = self._get_last_sunday_load()

        week_end_date = self._get_week_end_date(week_start_date)

        week = UserWeek(
            user_auth=self.user_auth,
            start_date=week_start_date,
            end_date=week_end_date,
            user_block=block,
            week_type=week_type,
            zone_focus=zone_focus,
            week_code=uuid.uuid4(),
            block_code=block.block_code,
        )
        week.temp_week_no = self.WEEK_NO
        self._set_week_data(
            week, block, starting_load, target_ramp_calculation_date, week_ramp_rate
        )

        week_days = self._create_week_days(week)
        pss_calc = PssCalculation(self.user_personalise_data, week)
        self._select_sessions_for_week_days(week, week_days[::-1], pss_calc)

        # According to the 2.15 section of CTP algorithm,
        # instead of the max load like we did before.
        # As week.sunday_max_load is passed as the previous sunday load value,
        # we assign the calculated planned load value to week.sunday_max_load
        week.sunday_max_load = self.DAYS[-1].planned_load

        self.WEEKS.append(week)
        return week

    def _get_week_end_date(self, week_start_date):
        week_end_date = week_start_date + timedelta(days=6)
        if get_date_from_datetime(week_end_date) > get_date_from_datetime(
            self.user_plan.end_date
        ):
            return self.user_plan.end_date
        return week_end_date

    def _create_block(self, number_of_weeks, block_start_date, block_zone_focus):
        self.BLOCK_NO += 1
        logger.info(f"Creating block no {self.BLOCK_NO}")

        user_block = UserBlock(
            user_auth=self.user_auth,
            user_plan=self.user_plan,
            plan_code=self.user_plan.plan_code,
            number=self.BLOCK_NO,
            no_of_weeks=number_of_weeks,
            block_code=uuid.uuid4(),
            zone_focus=block_zone_focus,
            start_date=block_start_date,
        )
        user_block.temp_user_block_no = self.BLOCK_NO
        week_start_date = block_start_date
        block_total_pss = Decimal(0.0)

        weeks_remaining = number_of_weeks
        while weeks_remaining > 0:
            week_type = self._get_week_type(weeks_remaining)
            week_zone_focus = self._get_week_zone_focus(week_type, block_zone_focus)

            week = self._create_week(
                week_start_date, user_block, week_zone_focus, week_type
            )
            block_total_pss += Decimal(week.planned_pss)
            week_start_date = week.end_date + timedelta(days=1)
            weeks_remaining -= 1

        user_block.planned_pss = block_total_pss
        user_block.end_date = self.WEEKS[-1].end_date
        self.BLOCKS.append(user_block)

    @staticmethod
    def _get_week_type(weeks_remaining):
        if weeks_remaining == 1:
            return RECOVERY_WEEK_TYPE
        return BUILD_WEEK_TYPE

    @staticmethod
    def _get_week_zone_focus(week_type, block_zone_focus):
        if week_type == BUILD_WEEK_TYPE:
            return block_zone_focus
        return 0

    def _create_blocks(self):
        total_weeks = get_total_weeks(
            self.user_plan.start_date, self.user_event.end_date
        )
        zone_focuses = get_zone_focuses(self.user_event)
        zone_focus_index = 0

        self._create_first_block(total_weeks, zone_focuses[zone_focus_index])
        zone_focus_index += 1
        if self.BLOCKS[-1].no_of_weeks < 3:
            # If first block is a broken block, then the zone focus of the block is not counted.
            # We will again start from the beginning
            zone_focus_index = 0

        total_possible_blocks = math.ceil(total_weeks / self.weeks_per_block)
        zone_focus_table_len = len(zone_focuses)

        # Create remaining blocks
        for _ in range(total_possible_blocks - 1):
            block_start_date = self.BLOCKS[-1].end_date + timedelta(days=1)
            block_zone_focus = zone_focuses[zone_focus_index]
            self._create_block(self.weeks_per_block, block_start_date, block_zone_focus)

            zone_focus_index += 1
            if zone_focus_index >= zone_focus_table_len:
                zone_focus_index = 0

    def _create_first_block(self, total_weeks, block_zone_focus):
        weeks_in_first_block = self._get_no_of_weeks_in_first_block(total_weeks)
        first_block_start_date = get_first_block_start_date(self.user_plan.start_date)
        self._create_block(
            weeks_in_first_block, first_block_start_date, block_zone_focus
        )

    def _get_weeks_per_block(self):
        user_age = self.user_personalise_data.get_age(self.user_plan.start_date)
        return get_weeks_per_block(age=user_age)

    def _get_no_of_weeks_in_first_block(self, total_weeks):
        weeks_in_first_block = total_weeks % self.weeks_per_block
        if not weeks_in_first_block:
            return self.weeks_per_block
        return weeks_in_first_block

    def create_training_plan(self):
        self._create_blocks()
        SaveTrainingPlan(
            self.BLOCKS, self.WEEKS, self.DAYS, self.SESSIONS
        ).store_data_in_db()


class SaveTrainingPlan:
    def __init__(self, blocks, weeks, days, sessions):
        self.BLOCKS = blocks
        self.WEEKS = weeks
        self.DAYS = days
        self.sessions = sessions

    def store_data_in_db(self):
        blocks = UserBlock.objects.bulk_create(self.BLOCKS)
        weeks = self._save_weeks(blocks)
        days = self._save_days(weeks)
        self._save_sessions(days)

    def _save_weeks(self, blocks):
        for week in self.WEEKS:
            block = blocks[week.temp_block_no - 1]
            week.user_block = block
        weeks = UserWeek.objects.bulk_create(self.WEEKS)
        return weeks

    def _save_days(self, weeks):
        for day in self.DAYS:
            week = weeks[day.temp_week_no - 1]
            day.user_week = week
        days = PlannedDay.objects.bulk_create(self.DAYS)
        return days

    def _save_sessions(self, days):
        for session in self.sessions:
            day = days[session.temp_day_no - 1]
            session.planned_day = day
        PlannedSession.objects.bulk_create(self.sessions)
