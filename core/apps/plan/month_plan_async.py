import asyncio
import datetime
from functools import partial, wraps

from core.apps.common.date_time_utils import DateTimeUtils

from .month_plan_utils import (
    DailyWeekFocusForMonth,
    SessionDetailsForMonth,
    UserAwayTilesForMonth,
)
from .session_edit_options_utils import SessionEditOptions


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


@async_wrap
def get_month_sessions_wrap(
    user, calendar_start_date, calendar_end_date, pro_feature_access
):
    session_details_obj = SessionDetailsForMonth(
        user, calendar_start_date, calendar_end_date, pro_feature_access
    )
    day_details_list = session_details_obj.day_details_for_month()
    return day_details_list


async def get_month_sessions(user, start_date, end_date, pro_feature_access):
    month_sessions = await get_month_sessions_wrap(
        user, start_date, end_date, pro_feature_access
    )
    return month_sessions


@async_wrap
def get_session_edit_options_wrap(user, calendar_start_date, calendar_end_date):
    user_profile_data = user.profile_data.filter(is_active=True).last()
    timezone_offset = user_profile_data.timezone.offset
    user_local_today = DateTimeUtils.get_user_local_date_from_utc(
        timezone_offset, datetime.datetime.now()
    )
    user_current_week = user.user_weeks.filter(
        start_date__lte=user_local_today, end_date__gte=user_local_today, is_active=True
    ).last()
    if not user_current_week:
        return []

    edit_options_obj = SessionEditOptions(user, user_current_week, user_local_today)
    edit_option_list = edit_options_obj.get_session_edit_options()
    return edit_option_list


async def get_session_edit_options(user, start_date, end_date):
    edit_options = await get_session_edit_options_wrap(user, start_date, end_date)
    return edit_options


@async_wrap
def get_user_away_tiles_wrap(
    user, calendar_start_date, calendar_end_date, pro_feature_access
):
    away_tiles_obj = UserAwayTilesForMonth(
        user, calendar_start_date, calendar_end_date, pro_feature_access
    )
    away_tiles_list = away_tiles_obj.away_tiles_for_month()
    return away_tiles_list


async def get_user_away_tiles(user, start_date, end_date, pro_feature_access):
    away_tiles_list = await get_user_away_tiles_wrap(
        user, start_date, end_date, pro_feature_access
    )
    return away_tiles_list


@async_wrap
def get_week_focus_wrap(
    user, calendar_start_date, calendar_end_date, pro_feature_access
):
    week_focus_obj = DailyWeekFocusForMonth(
        user, calendar_start_date, calendar_end_date, pro_feature_access
    )
    week_focus_list = week_focus_obj.week_focus_for_month()
    return week_focus_list


async def get_week_focus(user, start_date, end_date, pro_feature_access):
    week_focus_list = await get_week_focus_wrap(
        user, start_date, end_date, pro_feature_access
    )
    return week_focus_list


async def async_main(user, start_date, end_date, pro_feature_access):
    tasks1 = get_month_sessions(user, start_date, end_date, pro_feature_access)
    tasks2 = get_session_edit_options(user, start_date, end_date)
    tasks3 = get_user_away_tiles(user, start_date, end_date, pro_feature_access)
    tasks4 = get_week_focus(user, start_date, end_date, pro_feature_access)
    results = await asyncio.gather(tasks1, tasks2, tasks3, tasks4)
    data_dict = {
        "session_data": results[0],
        "edit_option_data": results[1],
        "away_tiles_data": results[2],
        "week_focus_data": results[3],
    }
    return data_dict
