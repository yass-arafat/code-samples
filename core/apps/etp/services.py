import calendar
import logging
import math
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import cycle

from core.apps.block.models import UserBlock
from core.apps.calculations.onboarding.ramp_rate_calculations import (
    get_calculated_ramp_rate,
)
from core.apps.common.const import (
    BUILD_WEEK_RAMP_RATE,
    MAX_TYPICAL_INTENSITY,
    MIN_AVAILABLE_TRAINING_HOUR,
    PSS_SL_MIN,
    RECOVERY_WEEK_RAMP_RATE,
    RECOVERY_WEEK_TYPE,
)
from core.apps.common.date_time_utils import daterange
from core.apps.common.utils import create_new_model_instance, update_is_active_value
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
    get_weeks_per_block,
    get_yesterdays_session_intensity,
    get_zone_focuses,
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
from core.apps.user_auth.models import UserAuthModel
from core.apps.week.models import UserWeek

logger = logging.getLogger(__name__)
calendar.setfirstweekday(calendar.MONDAY)


class EditTrainingPlan:
    def __init__(self, user_id, new_event_date, delete_goal=False):
        self.new_event_start_date = new_event_date
        self.delete_goal = delete_goal
        self.user_auth = UserAuthModel.objects.get(id=user_id, is_active=True)
        self.user_plan = self.user_auth.user_plans.filter(is_active=True).last()
        self.user_event = self.user_plan.user_event
        self.new_event_end_date = self._get_new_event_end_date()
        self.event_dates = self._get_user_event_dates()

        self.event_block = None

        self.user_personalise_data = self.user_auth.personalise_data.filter(
            is_active=True
        ).last()
        self.training_availability_object = TrainingAvailability(self.user_auth)
        self.user_age = self.user_personalise_data.get_age(self.user_plan.start_date)
        self.weeks_per_block = self._get_weeks_per_block()
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

        self.sunday_max_load = 0

    def _get_new_event_end_date(self):
        event_duration = (self.user_event.end_date - self.user_event.start_date).days
        return self.new_event_start_date + timedelta(days=event_duration)

    def _get_weeks_per_block(self):
        return get_weeks_per_block(self.user_age)

    def create_new_event(self):
        create_new_model_instance(self.user_event)
        self.user_event.start_date = self.new_event_start_date
        self.user_event.end_date = self.new_event_end_date
        self.user_event.save()

    def create_new_plan(self):
        create_new_model_instance(self.user_plan)
        self.user_plan.user_event = self.user_event
        self.user_plan.end_date = self.new_event_end_date
        self.user_plan.save()

    def get_valid_date(self, start_date):
        if self.delete_goal:
            # In case of delete goal, inactivation_start_date will always be from the next day of new event date
            return self.new_event_end_date + timedelta(days=1)
        if start_date < self.event_block.start_date:
            start_date = self.event_block.start_date
        if start_date <= datetime.today().date():
            start_date = datetime.today().date() + timedelta(days=1)
        return start_date

    @staticmethod
    def get_cyclic_list_at_value(target_list, value):
        cyclic_list = cycle(target_list)
        for _ in range(len(target_list)):
            if int(next(cyclic_list)) == value:
                return cyclic_list

    def inactivate_plan_after_new_goal_date(self, start_date):
        user_blocks = UserBlock.objects.filter(
            user_auth=self.user_auth, start_date__gte=start_date, is_active=True
        )
        user_weeks = UserWeek.objects.filter(
            user_auth=self.user_auth, start_date__gte=start_date, is_active=True
        )
        planned_days = PlannedDay.objects.filter(
            user_auth=self.user_auth, activity_date__gte=start_date, is_active=True
        )
        planned_sessions = PlannedSession.objects.filter(
            user_auth=self.user_auth, session_date_time__gte=start_date, is_active=True
        )

        update_is_active_value(user_blocks, False)
        update_is_active_value(user_weeks, False)
        update_is_active_value(planned_days, False)
        update_is_active_value(planned_sessions, False)

    def deactivate_plan_after_new_event_date(self):
        inactivation_start_date = self.get_valid_date(self.event_block.start_date)
        self.inactivate_plan_after_new_goal_date(inactivation_start_date)

    def get_yesterday(self, day):
        if len(self.DAYS) > 0:
            return self.DAYS[-1]
        yesterday_date = day.activity_date - timedelta(days=1)
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

    def create_week(self, week_start_date, week_end_date, block, zone_focus, week_type):
        ramp_rate = self._calculate_week_ramp_rate(week_start_date, week_type)
        starting_load = self.sunday_max_load
        sunday_max_load = starting_load + Decimal.from_float(ramp_rate)

        week = UserWeek(
            user_auth=self.user_auth,
            start_date=week_start_date,
            end_date=week_end_date,
            user_block=block,
            week_type=week_type,
            zone_focus=zone_focus,
            user_id=self.user_auth.code,
            week_code=uuid.uuid4(),
            block_code=block.block_code,
            sunday_max_load=sunday_max_load,
        )
        week.commute_pss_week = get_commute_pss_for_week(
            self.training_availability_object
        )
        return week

    @staticmethod
    def _calculate_week_ramp_rate(week_start_date, week_type):
        week_ramp_rate = (
            RECOVERY_WEEK_RAMP_RATE
            if week_type == RECOVERY_WEEK_TYPE
            else BUILD_WEEK_RAMP_RATE
        )
        return get_calculated_ramp_rate(week_start_date, week_ramp_rate)

    def create_week_days(self, week):
        activity_date = week.end_date
        target_load = week.sunday_max_load

        week_days = []
        number_of_week_days = get_number_of_week_days(week)
        for _ in range(number_of_week_days):
            day = PlannedDay(
                user_auth=self.user_auth,
                activity_date=activity_date,
                max_load=target_load,
                week_code=week.week_code,
                day_code=uuid.uuid4(),
                user_id=self.user_auth.code,
            )
            week_days.append(day)

            activity_date = day.activity_date - timedelta(days=1)
            target_load = calculate_target_load(day.max_load)
            day.temp_week_no = self.WEEK_NO

        days_with_session, sessions = self.select_sessions_for_week_days(
            week, week_days[::-1]
        )
        return days_with_session, sessions

    def check_rest_day(self, day, available_training_hour):
        return (
            self.user_had_session_for_last_three_days()
            or available_training_hour < MIN_AVAILABLE_TRAINING_HOUR
            or get_minimum_pss(day) < PSS_SL_MIN
            or day.activity_date in self.event_dates
        )

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

    def select_build_session(
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

    def select_sessions_for_week_days(self, week, days):
        week_days = []
        selected_sessions = []
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
            pss_calc = PssCalculation(self.user_personalise_data, week)

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

            available_training_hour = (
                self.training_availability_object.get_available_training_hour_for_day(
                    day.activity_date
                )
            )

            if self.check_rest_day(day, available_training_hour):
                day, session = self._set_as_rest_day(day, actual_yesterday)
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
        return week_days, selected_sessions

    def calculate_sunday_max_load(self):
        get_calculation_start_date = self.get_valid_date(self.event_block.start_date)
        previous_week_end_date = get_calculation_start_date - timedelta(days=1)
        previous_week = UserWeek.objects.filter(
            user_auth=self.user_auth,
            start_date__lte=previous_week_end_date,
            is_active=True,
        ).last()
        if previous_week:
            return previous_week.sunday_max_load
        return self.user_personalise_data.starting_load

    def create_weeks_days_sessions_for_incomplete_block(self):

        sessions_under_block = []
        weeks_dates = []
        block_pss = 0

        calculation_end_date = self.new_event_end_date
        calculation_start_date = self.get_valid_date(self.event_block.start_date)

        while calculation_start_date <= calculation_end_date:
            week_end_date = calculation_end_date
            week_start_date = self.get_valid_date(week_end_date - timedelta(days=6))
            weeks_dates.append(
                {"start_date": week_start_date, "end_date": week_end_date}
            )
            calculation_end_date = week_start_date - timedelta(days=1)

        total_weeks = len(weeks_dates)
        week_counter = 0
        week_type = "BUILD"
        zone_focus = self.event_block.zone_focus

        for week_date in weeks_dates[::-1]:
            week_counter += 1
            if week_counter == total_weeks:
                week_type = "RECOVERY"
                zone_focus = 0
            week = self.create_week(
                week_date["start_date"],
                week_date["end_date"],
                self.event_block,
                zone_focus,
                week_type,
            )

            week_days, week_sessions = self.create_week_days(week)

            self.sunday_max_load = week_days[-1].planned_load
            week.sunday_max_load = self.sunday_max_load
            week.planned_pss = Decimal(
                sum([session.planned_pss for session in week_sessions])
            )
            block_pss += week.planned_pss

            sessions_under_block += week_sessions
            self.WEEKS.append(week)

        self.SESSIONS += sessions_under_block
        return block_pss

    def edit_goal_backward(self):
        if self.user_plan.start_date > self.new_event_end_date:
            # This will happen if user deletes the goal the same day of creating the plan and didn't pair any ride.
            # We can deactivate every plan related entries in this case.
            self.inactivate_plan_after_new_goal_date(self.new_event_end_date)
            self.user_event.is_active = False
            self.user_event.save()
            self.user_plan.is_active = False
            self.user_plan.save()
            return

        self.event_block = self.user_auth.user_blocks.filter(
            is_active=True,
            start_date__lte=self.new_event_end_date,
            end_date__gte=self.new_event_end_date,
        ).last()

        if self.delete_goal:
            self.user_event.is_active = False
            self.user_event.save()
        else:
            self.create_new_event()
        self.create_new_plan()

        incomplete_block_start_date = self.event_block.start_date
        number_of_days_in_new_block = (
            self.new_event_end_date - incomplete_block_start_date
        )

        self.event_block = create_new_model_instance(self.event_block)
        self.event_block.no_of_weeks = max(
            math.ceil(number_of_days_in_new_block.days / 7), 1
        )
        self.event_block.end_date = self.new_event_end_date

        self.deactivate_plan_after_new_event_date()
        self.sunday_max_load = self.calculate_sunday_max_load()
        self.event_block.planned_pss = (
            self.create_weeks_days_sessions_for_incomplete_block()
        )

        self.BLOCKS.append(self.event_block)

        blocks = self.bulk_save_user_blocks()
        self.bulk_save_user_weeks(blocks)
        PlannedDay.objects.bulk_create(self.DAYS)
        PlannedSession.objects.bulk_create(self.SESSIONS)

    @staticmethod
    def get_last_sunday_max_load_for_block(block):
        blocks_last_week = UserWeek.objects.filter(block_code=block.block_code).last()
        return blocks_last_week.sunday_max_load

    def create_weeks_days_sessions_under_block(self, block):
        block_pss = 0

        number_of_weeks = block.no_of_weeks
        week_start_date = block.start_date
        while number_of_weeks > 0:
            if number_of_weeks == 1:
                week_type = "RECOVERY"
                zone_focus = 0
            else:
                week_type = "BUILD"
                zone_focus = block.zone_focus

            week_end_date = week_start_date + timedelta(days=6)
            week = self.create_week(
                week_start_date, week_end_date, block, zone_focus, week_type
            )

            week_days, week_sessions = self.create_week_days(week)
            week_start_date = week_end_date + timedelta(days=1)
            number_of_weeks -= 1

            self.sunday_max_load = week_days[-1].planned_load
            week.sunday_max_load = self.sunday_max_load
            week.planned_pss = Decimal(
                sum([session.planned_pss for session in week_sessions])
            )
            block_pss += week.planned_pss
            self.SESSIONS += week_sessions
            self.WEEKS.append(week)
        return block_pss

    def edit_goal_forward(self):
        self.create_new_event()
        self.create_new_plan()

        current_plan_last_block = UserBlock.objects.filter(
            plan_code=self.user_plan.plan_code, is_active=True
        ).last()
        self._create_blocks(current_plan_last_block)

        blocks = self.bulk_save_user_blocks()
        self.bulk_save_user_weeks(blocks)
        PlannedDay.objects.bulk_create(self.DAYS)
        PlannedSession.objects.bulk_create(self.SESSIONS)

    def _get_new_and_incomplete_blocks(self, current_plan_last_block, user_age):
        extended_days = self.new_event_end_date - current_plan_last_block.end_date
        weeks_per_block = get_weeks_per_block(user_age)
        number_of_new_block = int(extended_days.days / (weeks_per_block * 7))
        number_of_remaining_days = int(extended_days.days) % (weeks_per_block * 7)
        return number_of_new_block, number_of_remaining_days

    def _get_next_zone_focus(self, current_zone_focus):
        event_zone_focuses = get_zone_focuses(self.user_event)
        cyclic_list = cycle(event_zone_focuses)
        for _ in range(len(event_zone_focuses)):
            if int(next(cyclic_list)) == current_zone_focus:
                return cyclic_list

    def _create_blocks(self, current_plan_last_block):
        (
            number_of_new_blocks,
            number_of_remaining_days,
        ) = self._get_new_and_incomplete_blocks(current_plan_last_block, self.user_age)
        previous_block_end_date = current_plan_last_block.end_date
        block_number = current_plan_last_block.number
        zone_focus_cycled_list = self._get_next_zone_focus(
            current_plan_last_block.zone_focus
        )
        self.sunday_max_load = self.get_last_sunday_max_load_for_block(
            current_plan_last_block
        )

        for _ in range(number_of_new_blocks):
            block_number += 1
            zone_focus = next(zone_focus_cycled_list)
            previous_block_end_date = self._create_block(
                previous_block_end_date, zone_focus, block_number
            )

        if number_of_remaining_days:
            self._create_incomplete_block(
                previous_block_end_date, zone_focus_cycled_list, block_number + 1
            )

    def _create_block(self, previous_block_end_date, zone_focus, block_number):
        new_block_start_date = previous_block_end_date + timedelta(days=1)
        new_block_end_date = previous_block_end_date + timedelta(
            days=self.weeks_per_block * 7
        )

        block = UserBlock(
            user_auth=self.user_auth,
            user_plan=self.user_plan,
            number=block_number,
            no_of_weeks=self.weeks_per_block,
            zone_focus=zone_focus,
            block_code=uuid.uuid4(),
            start_date=new_block_start_date,
            end_date=new_block_end_date,
            plan_code=self.user_plan.plan_code,
            user_id=self.user_auth.code,
        )

        block_pss = self.create_weeks_days_sessions_under_block(block)
        block.planned_pss = block_pss
        self.BLOCKS.append(block)

        return new_block_end_date

    def _create_incomplete_block(
        self, previous_block_end_date, zone_focus_cycled_list, block_number
    ):
        incomplete_block_start_date = previous_block_end_date + timedelta(days=1)
        incomplete_block_end_date = self.new_event_end_date
        zone_focus = next(zone_focus_cycled_list)

        self.event_block = UserBlock(
            user_auth=self.user_auth,
            user_plan=self.user_plan,
            number=block_number,
            no_of_weeks=self.weeks_per_block,
            zone_focus=zone_focus,
            block_code=uuid.uuid4(),
            start_date=incomplete_block_start_date,
            end_date=incomplete_block_end_date,
            plan_code=self.user_plan.plan_code,
            user_id=self.user_auth.code,
        )

        self.event_block.planned_pss = (
            self.create_weeks_days_sessions_for_incomplete_block()
        )
        self.BLOCKS.append(self.event_block)

    def bulk_save_user_blocks(self):
        blocks = UserBlock.objects.bulk_create(self.BLOCKS)
        return blocks

    def bulk_save_user_weeks(self, blocks):
        for week in self.WEEKS:
            block_index = blocks.index(week.user_block)
            block = blocks[block_index]
            week.user_block = block
        UserWeek.objects.bulk_create(self.WEEKS)

    def _get_user_event_dates(self):
        """Returns list of dates under which the event will occur"""
        start_date = self.new_event_start_date
        end_date = self.new_event_end_date
        return [event_date for event_date in daterange(start_date, end_date)]
