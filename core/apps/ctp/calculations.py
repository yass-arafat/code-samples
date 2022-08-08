import calendar
import json
import logging
import math
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from math import e

from core.apps.calculations.evaluation.acute_load_services import AcuteLoadService
from core.apps.calculations.evaluation.load_services import LoadService
from core.apps.calculations.load_and_session_placement.commute_pss_calculations import (
    get_commute_pss_of_week,
)
from core.apps.calculations.load_and_session_placement.load_and_acute_load_post_commute_calculations import (
    get_acute_load_post_commute,
    get_load_post_commute,
)
from core.apps.calculations.load_and_session_placement.models.commute_pss_model import (
    CommutePSSModel,
)
from core.apps.calculations.load_and_session_placement.models.load_and_acute_load_post_commute_model import (
    AcuteLoadPostCommute,
    LoadPostCommuteModel,
)
from core.apps.common.common_functions import CommonClass, get_auto_update_start_date
from core.apps.common.const import MIN_STARTING_LOAD, MINIMUM_FRESHNESS
from core.apps.common.dictionary.planned_session_padding_limit_dictionary import (
    exclude_session_type_from_padding,
    padding_limit,
)
from core.apps.common.utils import initialize_dict
from core.apps.daily.models import PlannedDay
from core.apps.session.cached_truth_tables_utils import (
    get_rest_session,
    get_session_intervals_by_session,
    get_session_rule_by_session_type,
    get_session_type_by_session,
    get_session_types_by_zone_focus,
    get_sessions_by_session_type,
)
from core.apps.session.models import (
    ActualSession,
    PlannedSession,
    Session,
    SessionInterval,
)

logger = logging.getLogger(__name__)
calendar.setfirstweekday(calendar.MONDAY)


def get_weeks_per_block(age):
    return 3 if age >= 50 else 4


def get_total_weeks(start_date, end_date):
    first_week_start_date = start_date - timedelta(days=start_date.weekday())
    return math.ceil((end_date - first_week_start_date).days / 7)


def get_first_block_start_date(plan_start_date):
    return plan_start_date - timedelta(days=plan_start_date.weekday())


def get_zone_focuses(event):
    zone_focuses = event.event_type.ed_truth_table.get_zone_focuses()
    zone_focus_table = zone_focus_to_priority_table(zone_focuses)
    return zone_focus_table


def zone_focus_to_priority_table(zone_focuses):
    return [item[0].split("_")[0][-1] for item in zone_focuses]


def get_commute_pss_for_week(training_availability_object):
    single_commute_duration_hours = Decimal(
        training_availability_object.single_commute_duration_hours
    )
    commute_pss_model = CommutePSSModel(single_commute_duration_hours)
    commute_pss_week = get_commute_pss_of_week(
        commute_pss_model
    )  # this is a constant value refactor this
    return commute_pss_week


def get_load_constant():
    k_load = 42
    lambda_load = e ** (-1 / k_load)
    return Decimal(lambda_load)


def calculate_target_load(max_load):
    return max_load / get_load_constant()


def get_load_and_acute_load_post_commute_nth_day(day):
    load_post_commute_model = LoadPostCommuteModel(day)
    acute_load_post_commute_model = AcuteLoadPostCommute(day)
    return get_load_post_commute(load_post_commute_model), get_acute_load_post_commute(
        acute_load_post_commute_model
    )


def get_session_types_for_this_week(week):
    week_zone_focus = week.zone_focus
    session_types = get_session_types_by_zone_focus(week_zone_focus)
    return session_types


def get_minimum_pss(day):
    return min(
        day.training_pss_by_load,
        day.training_pss_by_freshness,
        day.training_pss_by_max_ride,
    )


def get_yesterdays_session_intensity(day, utp, auto_update_start_date=None):
    if utp:
        if day.activity_date == auto_update_start_date:
            if not day.yesterday:
                return 0
            user_yesterdays_session = ActualSession.objects.filter(
                is_active=True,
                day_code=day.yesterday.day_code,
                user_auth=day.user_auth,
            )
            if user_yesterdays_session:
                return user_yesterdays_session[0].actual_intensity  # check from db
            return 0
        else:
            return day.yesterday.selected_session.planned_intensity  # check from memory

    if day.yesterday:
        return day.yesterday.selected_session.planned_intensity  # check from memory
    return 0


def get_number_of_sessions_of_this_type_in_this_week(week_days, session_type):
    total_session = 0
    for day in week_days:
        if day.selected_session.session_type == session_type:
            total_session += 1
    return total_session


def select_session(day, session_type, zone_difficulty_service):
    sessions = get_sessions_by_session_type(session_type)
    for session in sessions:
        if session.difficulty_level is not None:
            zone_no = session.session_type.get_zone_focus()
            if zone_difficulty_service.is_session_difficulty_level_higher(
                zone_no, session.difficulty_level
            ):
                continue
        if session.pss <= day.training_pss_final_value:
            return session
    return None


def get_session_start_time(date):
    return datetime(date.year, date.month, date.day, 0, 0)


def pad_session(
    planned_day,
    session,
    selected_session,
    pad_interval,
    planned_time_in_power_zones,
    planned_time_in_hr_zones,
    available_training_hour,
):
    pss_difference = Decimal(planned_day.training_pss_final_value) - Decimal(
        session.planned_pss
    )
    intensity_mid_of_padding_interval = (
        pad_interval.ftp_percentage_lower + pad_interval.ftp_percentage_upper
    ) / 200

    tpad_in_hours = pss_difference / (
        100 * intensity_mid_of_padding_interval * intensity_mid_of_padding_interval
    )

    tpad_in_minutes = tpad_in_hours * 60

    session_type_code = selected_session.code
    if (
        session_type_code in padding_limit
        and tpad_in_minutes > padding_limit[session_type_code]
    ):
        tpad_in_minutes = Decimal(padding_limit[session_type_code])

    available_padding_time = (
        Decimal(available_training_hour * 60) - session.planned_duration
    )

    if tpad_in_minutes > available_padding_time:
        tpad_in_minutes = available_padding_time

    rounded_tpad_in_minutes = tpad_in_minutes - (tpad_in_minutes % 5)
    rounded_tpad_in_hours = rounded_tpad_in_minutes / 60
    pss_pad = (
        intensity_mid_of_padding_interval
        * intensity_mid_of_padding_interval
        * rounded_tpad_in_hours
        * 100
    )

    session.pad_time_in_seconds = rounded_tpad_in_minutes * 60
    session.pad_pss = pss_pad
    if rounded_tpad_in_minutes > 0:
        session.is_pad_applicable = True
    else:
        session.is_pad_applicable = False

    planned_time_in_power_zones[pad_interval.power_zone_focus]["value"] += int(
        session.pad_time_in_seconds
    )
    session.planned_time_in_power_zone = json.dumps(planned_time_in_power_zones)

    planned_time_in_hr_zones[pad_interval.heart_rate_zone_focus]["value"] += int(
        session.pad_time_in_seconds
    )
    session.planned_time_in_hr_zone = json.dumps(planned_time_in_hr_zones)

    session.planned_pss = session.planned_pss + pss_pad
    session.planned_duration = session.planned_duration + rounded_tpad_in_minutes

    planned_duration_in_hour = session.planned_duration / 60
    session_intensity = pow(
        session.planned_pss / (planned_duration_in_hour * 100), Decimal(0.5)
    )

    session.planned_intensity = session_intensity
    return session


def create_session_for_day(
    selected_session, session_type, day, available_training_hour, padding=False
):
    user_session_context = {
        "session_code": uuid.uuid4(),
        "day_code": day.day_code,
        "session_type": session_type,
        "name": selected_session.title or "",
        "user_auth": day.user_auth,
        "user_id": day.user_auth.code,
        "session_date_time": get_session_start_time(day.activity_date),
        "planned_duration": selected_session.duration_in_minutes,
        "planned_pss": selected_session.pss,
        "zone_focus": session_type.target_zone,
        "description": selected_session.description,
        "planned_intensity": selected_session.intensity,
    }
    session = PlannedSession(**user_session_context)

    planned_time_in_power_zones = initialize_dict(0, 8)
    planned_time_in_hr_zones = initialize_dict(0, 7)

    session_intervals = get_session_intervals_by_session(selected_session)
    pad_interval = None
    for session_interval in session_intervals:
        mid_ftp = (
            session_interval.ftp_percentage_upper
            + session_interval.ftp_percentage_lower
        ) / 2
        zone_focus = CommonClass.get_zone_focus_from_ftp(mid_ftp)
        planned_time_in_power_zones[zone_focus]["value"] += int(
            session_interval.time_in_seconds
        )

        # TODO: session_interval model has method for fetching zone focus
        if session_interval.fthr_percentage_upper == 999:
            mid_fthr = session_interval.fthr_percentage_lower
        else:
            mid_fthr = (
                session_interval.fthr_percentage_lower
                + session_interval.fthr_percentage_upper
            ) / 2
        zone_focus = CommonClass.get_zone_focus_from_fthr(mid_fthr)
        planned_time_in_hr_zones[zone_focus]["value"] += int(
            session_interval.time_in_seconds
        )
        if session_interval.is_padding_interval:
            pad_interval = session_interval

    if padding and pad_interval:
        session = pad_session(
            day,
            session,
            selected_session,
            pad_interval,
            planned_time_in_power_zones,
            planned_time_in_hr_zones,
            available_training_hour,
        )
    else:
        session.planned_time_in_power_zone = json.dumps(planned_time_in_power_zones)
        session.planned_time_in_hr_zone = json.dumps(planned_time_in_hr_zones)

    return session


def set_as_rest_day(
    plan, day, user_personalise_data, utp, actual_yesterday, auto_update_start_date=None
):
    rest_session = get_rest_session()
    session_type = get_session_type_by_session(rest_session)
    session = create_session_for_day(
        rest_session, session_type, day, None, padding=False
    )
    day = final_load_calculation_for_day(
        plan,
        day,
        session,
        actual_yesterday,
        user_personalise_data,
        utp,
        auto_update_start_date,
    )
    day.zone_focus = session.session_type.target_zone
    session.session = rest_session
    day.selected_session = session
    return day, session


def final_load_calculation_for_day(
    plan,
    day,
    session,
    actual_yesterday,
    user_personalise_data,
    utp=False,
    auto_update_start_date=None,
):
    pss_total = day.commute_pss_day + session.planned_pss
    if utp and day.activity_date == auto_update_start_date and actual_yesterday:
        previous_load = max(MIN_STARTING_LOAD, actual_yesterday.actual_load)
        previous_acute_load = actual_yesterday.actual_acute_load
    elif day.activity_date == plan.start_date:
        previous_load = user_personalise_data.starting_load
        previous_acute_load = user_personalise_data.starting_acute_load
    else:
        previous_load = day.yesterday.planned_load
        previous_acute_load = day.yesterday.planned_acute_load

    day.planned_pss = pss_total
    day.planned_load = LoadService(previous_load, pss_total).get_planned_load()
    day.planned_acute_load = AcuteLoadService(
        previous_acute_load, pss_total
    ).get_planned_acute_load()
    return day


class PssCalculation:
    def __init__(
        self, user_personalise_data, week, utp=False, auto_update_start_date=None
    ):
        self.k_load = 42
        self.lambda_load = Decimal(e ** (-1 / self.k_load))
        self.k_acute_load = 7
        self.lambda_acute_load = Decimal(e ** (-1 / self.k_acute_load))
        self.const_max_single_ride_multiplier = Decimal(3.6)
        self.const_multiplier = Decimal(100.00)
        self.utp = utp

        # TODO: Only pass commute_pss_week
        self.user_week = week

        self.starting_load = user_personalise_data.starting_load
        self.starting_acute_load = user_personalise_data.starting_acute_load

        self.auto_update_start_date = (
            auto_update_start_date or get_auto_update_start_date()
        )

    def get_commute_pss_of_day(self, day, commute_days_list):
        if not commute_days_list[day.activity_date.weekday()]:
            return 0
        return self.user_week.commute_pss_week

    def get_load_and_acute_load_post_commute_nth_day(self, day, actual_yesterday=None):
        if day.yesterday:
            if (
                self.utp
                and day.activity_date == self.auto_update_start_date
                and actual_yesterday
            ):
                load = max(actual_yesterday.actual_load, MIN_STARTING_LOAD)
                acute_load = actual_yesterday.actual_acute_load
            else:
                load = day.yesterday.planned_load
                acute_load = day.yesterday.planned_acute_load
        else:
            load = self.starting_load
            acute_load = self.starting_acute_load
        load_post_commute = (
            self.lambda_load * load + (1 - self.lambda_load) * day.commute_pss_day
        )
        acute_load_post_commute = (
            self.lambda_acute_load * acute_load
            + (1 - self.lambda_acute_load) * day.commute_pss_day
        )

        return load_post_commute, acute_load_post_commute

    def get_training_pss_load(self, day, actual_yesterday=None):
        if day.yesterday:
            if (
                self.utp
                and day.activity_date == self.auto_update_start_date
                and actual_yesterday
            ):
                load = max(actual_yesterday.actual_load, MIN_STARTING_LOAD)
            else:
                load = day.yesterday.planned_load
        else:
            load = self.starting_load
        return (day.max_load - load * self.lambda_load) / (
            1 - self.lambda_load
        ) - day.commute_pss_day

    def get_training_pss_freshness(self, day, actual_yesterday=None):
        pss_commute = day.commute_pss_day
        if day.yesterday:
            if (
                self.utp
                and day.activity_date == self.auto_update_start_date
                and actual_yesterday
            ):
                load = max(actual_yesterday.actual_load, MIN_STARTING_LOAD)
                acute_load = actual_yesterday.actual_acute_load
            else:
                load = day.yesterday.planned_load
                acute_load = day.yesterday.planned_acute_load
        else:
            load = self.starting_load
            acute_load = self.starting_acute_load

        return (
            (
                MINIMUM_FRESHNESS
                - (self.lambda_load * load)
                + (self.lambda_acute_load * acute_load)
            )
            / (self.lambda_acute_load - self.lambda_load)
        ) - pss_commute

    def get_training_pss_max_ride(self, day, actual_yesterday=None):
        if day.yesterday:
            if (
                self.utp
                and day.activity_date == self.auto_update_start_date
                and actual_yesterday
            ):
                load = max(actual_yesterday.actual_load, MIN_STARTING_LOAD)
            else:
                load = day.yesterday.planned_load
        else:
            load = self.starting_load
        # Load can not be lower than MIN_STARTING_LOAD
        load = max(load, MIN_STARTING_LOAD)

        return self.const_max_single_ride_multiplier * load - day.commute_pss_day

    @staticmethod
    def get_available_training_hours_of_day_for_user(date, user_available_hours_list):
        return Decimal(user_available_hours_list[date.weekday()])

    def get_training_pss_available_hours(
        self, session_type, day, user_available_hours_list
    ):
        intensity = get_session_rule_by_session_type(session_type).typical_intensity
        min_training_hours = self.get_available_training_hours_of_day_for_user(
            day.activity_date, user_available_hours_list
        )
        training_pss_avail_hours = (
            pow(intensity, 2) * min_training_hours * self.const_multiplier
        )
        return training_pss_avail_hours


def get_number_of_week_days(week):
    if type(week.start_date) == datetime:
        start_date = week.start_date.date()
    else:
        start_date = week.start_date

    if type(week.end_date) == datetime:
        end_date = week.end_date.date()
    else:
        end_date = week.end_date

    return (end_date - start_date).days + 1


def is_pad_applicable(planned_day: PlannedDay, selected_session: Session):
    return bool(
        planned_day.training_pss_final_value > selected_session.pss
        and selected_session.session_type.code not in exclude_session_type_from_padding
        and SessionInterval.objects.filter(
            session=selected_session, is_padding_interval=True
        ).exists()
    )
