from datetime import datetime

from core.apps.activities.utils import dakghor_get_athlete_activity
from core.apps.common.common_functions import get_date_from_datetime
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.daily.models import PlannedDay
from core.apps.daily.utils import is_day_completed
from core.apps.session.models import (
    ActualSession,
    PlannedSession,
    UserAway,
    UserAwayInterval,
)
from core.apps.week.models import UserWeek

from .api.base.serializers import (
    ActualSessionSerializer,
    AwayTileSerializerClass,
    GetMyMonthPlanSerializer,
    PlannedSessionSerializer,
)
from .dictionary import get_week_focus_dictionary


def get_day_details_for_month(user, start_date, end_date):
    month_plan_dict = []
    user_last_plan = user.user_plans.filter(is_active=True).last()
    user_last_event = user_last_plan.user_event

    if get_date_from_datetime(end_date) > user_last_event.end_date:
        end_date = user_last_event.end_date

    if get_date_from_datetime(start_date) > user_last_event.end_date:
        days = []
    else:
        days = user.planned_days.filter(
            activity_date__range=(start_date, end_date), is_active=True
        ).order_by("activity_date")

    timezone_offset = user.timezone_offset

    planned_sessions = user.planned_sessions.filter(
        session_date_time__date__range=(start_date, end_date), is_active=True
    ).order_by("session_date_time")

    user_current_week = user.user_weeks.filter(
        start_date__lte=datetime.today(), end_date__gte=datetime.today(), is_active=True
    ).last()
    user_local_today = DateTimeUtils.get_user_local_date_from_utc(
        user.timezone_offset, datetime.now()
    )

    session_movable_days = []
    current_week_planned_sessions = {}
    week_days_session_intensities = []
    if user_current_week:
        session_movable_days = PlannedDay.objects.filter(
            week_code=user_current_week.week_code,
            activity_date__gte=user_local_today,
            is_active=True,
        ).order_by("activity_date")
        current_week_planned_sessions = get_sessions_for_movable_days(
            session_movable_days, planned_sessions
        )
        week_days_session_intensities = calculate_week_days_session_intensities(
            user_current_week, user_local_today
        )

    user_actual_sessions = ActualSession.objects.filter_actual_sessions(user_auth=user)
    user_planned_sessions = PlannedSession.objects.filter(
        user_auth=user, is_active=True
    ).exclude(session_type__code="REST")
    weeks_cache = {}
    user_plans_cache = {}
    total_blocks_cache = {}

    for index, day in enumerate(days):
        # It is kept as array because in future if there we support multiple session in one day we need list
        day_sessions = []
        planned_session = planned_sessions[index]

        is_completed_day = user_actual_sessions.filter(day_code=day.day_code).exists()

        if day.week_code in weeks_cache:
            week = weeks_cache[day.week_code]
        else:
            week = UserWeek.objects.get(week_code=day.week_code, is_active=True)
            weeks_cache[week.week_code] = week

        if week.block_code in user_plans_cache:
            user_plan = user_plans_cache[week.block_code]
        else:
            user_block = user.user_blocks.filter(
                block_code=week.block_code, is_active=True
            ).last()
            user_plan = user.user_plans.filter(
                plan_code=user_block.plan_code, is_active=True
            ).last()
            user_plans_cache[week.block_code] = user_plan

        if user_plan.plan_code in total_blocks_cache:
            total_blocks = total_blocks_cache[user_plan.plan_code]
        else:
            total_blocks = user.user_blocks.filter(
                plan_code=user_plan.plan_code, is_active=True
            ).count()
            total_blocks_cache[user_plan.plan_code] = total_blocks

        serialized_session = GetMyMonthPlanSerializer(
            planned_session,
            context={
                "offset": timezone_offset,
                "is_completed_day": is_completed_day,
                "current_week": user_current_week,
                "user_actual_sessions": user_actual_sessions,
                "week_days_session_intensities": week_days_session_intensities,
                "user_today": user_local_today,
                "user": user,
                "session_movable_days": session_movable_days,
                "current_week_planned_sessions": current_week_planned_sessions,
                "user_planned_sessions": user_planned_sessions,
            },
        )

        day_sessions.append(serialized_session.data)

        week_focus = get_week_focus_dictionary(user, week, total_blocks)

        month_plan_dict.append(
            {
                "date": DateTimeUtils.get_user_local_date_from_utc(
                    timezone_offset,
                    datetime.combine(day.activity_date, datetime.min.time()),
                ),
                "zone_focus": day.zone_focus,
                "is_completed": is_completed_day,
                "week_focus": week_focus,
                "day_sessions": day_sessions,
            }
        )

    return month_plan_dict


def calculate_week_days_session_intensities(week, today):
    days = PlannedDay.objects.filter(week_code=week.week_code, is_active=True)
    intensities = [0] * 7
    for day in days:
        session = get_session(day, today)
        if session:
            actual_session = session.actual_session
            if actual_session:
                intensities[
                    day.activity_date.weekday()
                ] = actual_session.actual_intensity
            else:
                intensities[day.activity_date.weekday()] = session.planned_intensity
    return intensities


def get_session(day, today):
    session = (
        PlannedSession.objects.filter(day_code=day.day_code, is_active=True)
        .exclude(session_type__code="REST")
        .first()
    )
    if session:
        if (
            day.activity_date < today and not session.is_completed
        ):  # if past day session is not completed then it is a rest day
            return None
        else:
            return session
    else:
        return None


def get_sessions_for_movable_days(session_moveable_days, planned_sessions):
    sessions_for_movable_days = {}
    for day in session_moveable_days:
        session = planned_sessions.filter(day_code=day.day_code, is_active=True).first()
        sessions_for_movable_days[day.day_code] = session
    return sessions_for_movable_days


def day_details_for_month(user, start_date, end_date):
    month_plan_dict = []
    timezone_offset = user.timezone_offset
    planned_days, unplanned_days = get_planned_and_unplanned_days(
        user, start_date, end_date
    )
    planned_sessions = user.planned_sessions.filter(
        session_date_time__date__range=(start_date, end_date), is_active=True
    ).order_by("session_date_time")

    user_current_week = user.user_weeks.filter(
        start_date__lte=datetime.today(), end_date__gte=datetime.today(), is_active=True
    ).last()
    user_local_today = DateTimeUtils.get_user_local_date_from_utc(
        user.timezone_offset, datetime.now()
    )
    user_away_days = UserAway.objects.filter(user_auth=user, is_active=True).order_by(
        "away_date"
    )
    away_interval_codes = list(user_away_days.values_list("interval_code", flat=True))
    away_dates_flat_list = list(user_away_days.values_list("away_date", flat=True))
    all_away_intervals = UserAwayInterval.objects.filter(
        interval_code__in=away_interval_codes, is_active=True
    )

    session_movable_days = []
    current_week_planned_sessions = {}
    week_days_session_intensities = []
    if user_current_week:
        session_movable_days = (
            PlannedDay.objects.filter(
                week_code=user_current_week.week_code,
                activity_date__gte=user_local_today,
                is_active=True,
            )
            .order_by("activity_date")
            .exclude(activity_date__in=away_dates_flat_list)
        )
        current_week_planned_sessions = get_sessions_for_movable_days(
            session_movable_days, planned_sessions
        )
        week_days_session_intensities = calculate_week_days_session_intensities(
            user_current_week, user_local_today
        )

    user_actual_sessions = ActualSession.objects.filter_actual_sessions(user_auth=user)
    user_planned_sessions = PlannedSession.objects.filter(
        user_auth=user, is_active=True
    ).exclude(session_type__code="REST")

    weeks_cache = {}
    user_plans_cache = {}
    total_blocks_cache = {}

    for day in unplanned_days:
        day_sessions = []
        actual_sessions = user_actual_sessions.filter(
            session_date_time__date=day.activity_date
        ).select_related("third_party")
        if actual_sessions:
            for actual_session in actual_sessions:
                ride_summary = None
                if actual_session.athlete_activity_code:
                    athlete_activity = dakghor_get_athlete_activity(
                        actual_session.athlete_activity_code
                    ).json()["data"]["athlete_activity"]
                    ride_summary = athlete_activity["ride_summary"]

                serialized_session = ActualSessionSerializer(
                    actual_session,
                    context={
                        "offset": timezone_offset,
                        "activity_type": actual_session.activity_type,
                        "ride_summary": ride_summary,
                        "current_week": user_current_week,
                        "week_days_session_intensities": week_days_session_intensities,
                        "user_today": user_local_today,
                        "user": user,
                        "session_movable_days": session_movable_days,
                        "current_week_planned_sessions": current_week_planned_sessions,
                        "user_planned_sessions": user_planned_sessions,
                    },
                )
                day_sessions.append(serialized_session.data)

        month_plan_dict.append(
            {
                "date": DateTimeUtils.get_user_local_date_from_utc(
                    timezone_offset,
                    datetime.combine(day.activity_date, datetime.min.time()),
                ),
                "zone_focus": None,
                "is_completed": False,
                "week_focus": {},
                "day_sessions": day_sessions,
            }
        )

    for day in planned_days:
        day_sessions = []
        day_zone_focus = day.zone_focus
        actual_sessions = user_actual_sessions.filter(
            session_date_time__date=day.activity_date
        ).select_related("third_party")

        is_completed_day = is_day_completed(day.activity_date, user)
        if day.week_code in weeks_cache:
            week = weeks_cache[day.week_code]
        else:
            week = UserWeek.objects.get(week_code=day.week_code, is_active=True)
            weeks_cache[week.week_code] = week

        if week.block_code in user_plans_cache:
            user_plan = user_plans_cache[week.block_code]
        else:
            user_block = user.user_blocks.filter(
                block_code=week.block_code, is_active=True
            ).last()
            user_plan = user.user_plans.filter(
                plan_code=user_block.plan_code, is_active=True
            ).last()
            user_plans_cache[week.block_code] = user_plan

        if user_plan.plan_code in total_blocks_cache:
            total_blocks = total_blocks_cache[user_plan.plan_code]
        else:
            total_blocks = user.user_blocks.filter(
                plan_code=user_plan.plan_code, is_active=True
            ).count()
            total_blocks_cache[user_plan.plan_code] = total_blocks

        away_day = user_away_days.filter(away_date=day.activity_date).first()

        if away_day:
            away_interval = all_away_intervals.filter(
                is_active=True, interval_code=away_day.interval_code
            ).first()
            serialized_away_tile = AwayTileSerializerClass(
                user, away_day, away_interval
            )
            day_sessions.append(serialized_away_tile.get_data())
            is_completed_day = False
            day_zone_focus = None
        else:
            planned_session = PlannedSession.objects.filter(
                user_auth=user,
                session_date_time__date=day.activity_date,
                is_active=True,
            ).last()
            if (
                planned_session.zone_focus == 0
                or planned_session.actual_session is None
            ):
                serialized_planned_session = PlannedSessionSerializer(
                    planned_session,
                    context={
                        "offset": timezone_offset,
                        "is_completed_day": is_completed_day,
                        "current_week": user_current_week,
                        "week_days_session_intensities": week_days_session_intensities,
                        "user_today": user_local_today,
                        "user": user,
                        "session_movable_days": session_movable_days,
                        "current_week_planned_sessions": current_week_planned_sessions,
                        "user_planned_sessions": user_planned_sessions,
                    },
                )

                day_sessions.append(serialized_planned_session.data)

        if actual_sessions:
            for actual_session in actual_sessions:
                planned_session = actual_session.planned_session
                if planned_session and planned_session.zone_focus == 0:
                    continue

                ride_summary = None
                if actual_session.athlete_activity_code:
                    athlete_activity = dakghor_get_athlete_activity(
                        actual_session.athlete_activity_code
                    ).json()["data"]["athlete_activity"]
                    ride_summary = athlete_activity["ride_summary"]

                serialized_session = ActualSessionSerializer(
                    actual_session,
                    context={
                        "offset": timezone_offset,
                        "activity_type": actual_session.activity_type,
                        "ride_summary": ride_summary,
                        "is_completed_day": is_completed_day,
                        "current_week": user_current_week,
                        "week_days_session_intensities": week_days_session_intensities,
                        "user_today": user_local_today,
                        "user": user,
                        "session_movable_days": session_movable_days,
                        "current_week_planned_sessions": current_week_planned_sessions,
                        "user_planned_sessions": user_planned_sessions,
                    },
                )
                day_sessions.append(serialized_session.data)

        week_focus = get_week_focus_dictionary(user, week, total_blocks)

        month_plan_dict.append(
            {
                "date": DateTimeUtils.get_user_local_date_from_utc(
                    timezone_offset,
                    datetime.combine(day.activity_date, datetime.min.time()),
                ),
                "zone_focus": day_zone_focus,
                "is_completed": is_completed_day,
                "week_focus": week_focus,
                "day_sessions": day_sessions,
            }
        )

    return month_plan_dict


def get_planned_and_unplanned_days(user, start_date, end_date):
    planned_days = user.planned_days.filter(
        activity_date__range=(start_date, end_date), is_active=True
    ).order_by("activity_date")
    planned_activity_dates = [day.activity_date for day in planned_days]
    unplanned_days = user.actual_days.filter(
        activity_date__range=(start_date, end_date), is_active=True
    ).exclude(activity_date__in=planned_activity_dates)

    return planned_days, unplanned_days


def is_previous_goal_completed(user):
    """Checks if the user's previous goal was completed (i.e. the event date expired) or not"""
    return bool(user.user_plans.filter())
