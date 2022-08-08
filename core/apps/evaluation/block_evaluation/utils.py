import calendar
import datetime
from datetime import timedelta

from core.apps.block.models import UserBlock
from core.apps.common.common_functions import get_date_from_datetime
from core.apps.session.models import ActualSession, PlannedSession, UserAway
from core.apps.session.utils import (
    get_block_session_dict,
    map_actual_session_into_planned_session,
)

from .dictionary import get_single_block_session_dictionary

calendar.setfirstweekday(calendar.MONDAY)


# Depreciated from R7
def get_total_blocks(onboarding_date, event_date_time, user):
    week_day = calendar.weekday(
        onboarding_date.year, onboarding_date.month, onboarding_date.day
    )

    start_date = onboarding_date - timedelta(days=week_day)
    user_block_list = UserBlock.objects.filter(
        start_date__range=(start_date, event_date_time.date()),
        user_auth=user,
        is_active=True,
    ).order_by("start_date")
    training_block_evaluation_dict = {"tb_load_graph_data": []}
    timezone_offset = user.timezone_offset

    user_away_dates = list(
        UserAway.objects.filter(user_auth=user, is_active=True).values_list(
            "away_date", flat=True
        )
    )
    planned_sessions = (
        PlannedSession.objects.filter(user_auth=user, is_active=True)
        .exclude(session_date_time__in=user_away_dates)
        .select_related("session_type")
        .order_by("session_date_time")
    )

    actual_sessions = (
        ActualSession.objects.filter(user_auth=user, is_active=True)
        .select_related("session_score")
        .order_by("session_date_time", "third_party__priority")
    )
    block_session_dict_arr = map_actual_session_into_planned_session(
        planned_sessions=planned_sessions,
        actual_sessions=actual_sessions,
        timezone_offset=timezone_offset,
    )

    user_in_block = None
    for idx, user_block in enumerate(user_block_list):
        if user_block.start_date <= datetime.date.today() <= user_block.end_date:
            user_in_block = idx

        block_end_date = user_block.end_date
        if get_date_from_datetime(user_block.end_date) > get_date_from_datetime(
            event_date_time
        ):
            block_end_date = event_date_time.date()
        current_block_session_dict_arr = [
            di
            for di in block_session_dict_arr
            if user_block.start_date <= di["date"] <= block_end_date
        ]

        month_no = user_block.start_date.month
        recovery_week_no = 1
        building_week_no = user_block.no_of_weeks - 1

        single_block_dict = get_single_block_session_dictionary(
            user_block.zone_focus,
            month_no,
            user_block.is_completed,
            user_block.planned_pss,
            building_week_no,
            recovery_week_no,
            current_block_session_dict_arr,
        )
        training_block_evaluation_dict["tb_load_graph_data"].append(single_block_dict)

    training_block_evaluation_dict["current_block"] = user_in_block

    return training_block_evaluation_dict


def get_user_blocks(onboarding_date, event_date_time, user):
    week_day = calendar.weekday(
        onboarding_date.year, onboarding_date.month, onboarding_date.day
    )

    start_date = onboarding_date - timedelta(days=week_day)
    user_block_list = UserBlock.objects.filter(
        start_date__range=(start_date, event_date_time.date()),
        user_auth=user,
        is_active=True,
    ).order_by("start_date")
    training_block_evaluation_dict = {"tb_load_graph_data": []}

    user_away_dates = list(
        UserAway.objects.filter(user_auth=user, is_active=True).values_list(
            "away_date", flat=True
        )
    )
    planned_sessions = (
        PlannedSession.objects.filter(user_auth=user, is_active=True)
        .exclude(session_date_time__in=user_away_dates)
        .select_related("session_type")
        .order_by("session_date_time")
    )

    block_session_dict_arr = get_block_session_dict(
        planned_sessions=planned_sessions, user=user
    )

    user_in_block = None
    for idx, user_block in enumerate(user_block_list):
        if user_block.start_date <= datetime.date.today() <= user_block.end_date:
            user_in_block = idx

        block_end_date = user_block.end_date
        if get_date_from_datetime(user_block.end_date) > get_date_from_datetime(
            event_date_time
        ):
            block_end_date = event_date_time.date()
        current_block_session_dict_arr = [
            di
            for di in block_session_dict_arr
            if user_block.start_date <= di["session_date_time"].date() <= block_end_date
        ]

        month_no = user_block.start_date.month
        recovery_week_no = 1
        building_week_no = user_block.no_of_weeks - 1

        single_block_dict = get_single_block_session_dictionary(
            user_block.zone_focus,
            month_no,
            user_block.is_completed,
            user_block.planned_pss,
            building_week_no,
            recovery_week_no,
            current_block_session_dict_arr,
        )
        training_block_evaluation_dict["tb_load_graph_data"].append(single_block_dict)

    training_block_evaluation_dict["current_block"] = user_in_block

    return training_block_evaluation_dict
