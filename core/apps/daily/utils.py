import datetime
import logging
from decimal import Decimal
from math import e

from django.db.models import Sum

from core.apps.common.common_functions import get_current_plan
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.utils import log_extra_fields
from core.apps.session.models import ActualSession, PlannedSession, UserAway

from .dictionary import get_past_ride_dict, get_upcoming_ride_dict
from .models import ActualDay
from .serializers import DayActualSessionSerializer, DayPlannedSessionSerializer

logger = logging.getLogger(__name__)


def get_load_constant():
    k_load = 42
    lambda_load = e ** (-1 / k_load)
    return Decimal(lambda_load)


def get_acute_load_constant():
    k_acute_load = 7
    return Decimal(e ** (-1 / k_acute_load))


# Depreciated from R7
def get_upcoming_and_past_ride_dict_array(
    planned_sessions, user_utc_today, timezone_offset
):
    past_rides_dict_arr = []
    upcoming_rides_dict_arr = []
    previous_rides, upcoming_rides = get_previous_and_upcoming_rides(
        planned_sessions, user_utc_today
    )

    for planned_session in previous_rides:
        planned_duration = planned_session.session_duration / 60  # Depreciated from R7
        session_timespan = planned_session.session_duration * 60

        actual_session = planned_session.actual_session

        past_rides_dict_arr.append(
            get_past_ride_dict(
                planned_session,
                session_timespan,
                DateTimeUtils.get_user_local_date_from_utc(
                    timezone_offset, planned_session.session_date_time
                ),
                planned_duration,
                actual_session,
            )
        )

    for planned_session in upcoming_rides:
        planned_duration = planned_session.planned_duration / 60  # Depreciated from R7
        session_timespan = planned_session.planned_duration * 60

        upcoming_rides_dict_arr.append(
            get_upcoming_ride_dict(
                planned_session,
                session_timespan,
                DateTimeUtils.get_user_local_date_from_utc(
                    timezone_offset, planned_session.session_date_time
                ),
                planned_duration,
            )
        )

    return upcoming_rides_dict_arr, past_rides_dict_arr


# Depreciated from R7
def get_today_session_details(user_auth, user_utc_today):
    try:
        user_away_dates = list(
            UserAway.objects.filter(user_auth=user_auth, is_active=True).values_list(
                "away_date", flat=True
            )
        )
        planned_sessions = PlannedSession.objects.filter(
            user_auth=user_auth, is_active=True
        ).exclude(session_date_time__in=user_away_dates)
        timezone_offset = user_auth.timezone_offset

        rides_completed, rides_total = get_rides_completed_and_total(
            user_auth, planned_sessions
        )

        (
            upcoming_rides_dict_arr,
            past_rides_dict_arr,
        ) = get_upcoming_and_past_ride_dict_array(
            planned_sessions, user_utc_today, timezone_offset
        )

    except Exception as e:
        logger.exception("Could not found today details" + str(e))
        rides_completed, rides_total, upcoming_rides_dict_arr, past_rides_dict_arr = (
            0,
            0,
            [],
            [],
        )
    return rides_completed, rides_total, upcoming_rides_dict_arr, past_rides_dict_arr


def upcoming_and_past_rides(
    planned_sessions, user_local_date, user, upcoming_rides_count=3
):
    past_rides_dict_arr = []
    upcoming_rides_dict_arr = []
    previous_rides, upcoming_rides = get_previous_and_upcoming_rides(
        planned_sessions, user_local_date, upcoming_rides_count
    )

    for planned_session in upcoming_rides:
        upcoming_rides_dict_arr.append(
            DayPlannedSessionSerializer(
                planned_session,
                context={
                    "user": user,
                    # 'event_dates': event_dates,
                },
            ).data
        )

    for planned_session in previous_rides:
        actual_session = planned_session.actual_session
        if actual_session and not planned_session.is_recovery_session():
            past_rides_dict_arr.append(
                DayActualSessionSerializer(
                    actual_session,
                    context={
                        "user": user,
                        # 'event_dates': event_dates,
                    },
                ).data
            )
        else:
            past_rides_dict_arr.append(
                DayPlannedSessionSerializer(
                    planned_session,
                    context={
                        "user": user,
                        # 'event_dates': event_dates,
                    },
                ).data
            )

    return upcoming_rides_dict_arr, past_rides_dict_arr


def today_session_details(user_auth, user_local_date):
    """Returns today details info for home page when user has an active goal"""
    upcoming_rides_dict_arr = []
    past_rides_dict_arr = []
    planned_sessions = None

    try:
        user_away_dates = list(
            UserAway.objects.filter(user_auth=user_auth, is_active=True).values_list(
                "away_date", flat=True
            )
        )
        current_plan = get_current_plan(user_auth)
        if current_plan:
            planned_sessions = PlannedSession.objects.filter(
                user_auth=user_auth,
                is_active=True,
                session_date_time__date__gte=current_plan.start_date,
                session_date_time__date__lte=current_plan.end_date,
            ).exclude(session_date_time__in=user_away_dates)

        rides_completed, rides_total = get_rides_completed_and_total(
            user_auth, planned_sessions
        )

        if planned_sessions:
            upcoming_rides_dict_arr, past_rides_dict_arr = upcoming_and_past_rides(
                planned_sessions, user_local_date, user_auth
            )

    except Exception as e:
        logger.exception("Could not found today details" + str(e))
        rides_completed, rides_total, upcoming_rides_dict_arr, past_rides_dict_arr = (
            0,
            0,
            [],
            [],
        )
    return rides_completed, rides_total, upcoming_rides_dict_arr, past_rides_dict_arr


def get_rides_completed_and_total(user_auth, planned_sessions=None):
    """Planned session code without rest session"""
    if planned_sessions is None:
        planned_sessions_code = (
            PlannedSession.objects.filter(user_auth=user_auth, is_active=True)
            .exclude(zone_focus=0)
            .values("session_code")
        )
    else:
        planned_sessions_code = planned_sessions.exclude(zone_focus=0).values(
            "session_code"
        )

    rides_completed = (
        ActualSession.objects.filter(
            user_auth=user_auth, session_code__in=planned_sessions_code, is_active=True
        )
        .distinct("session_code")
        .count()
    )

    rides_total = planned_sessions_code.count()

    return rides_completed, rides_total


def get_current_prs(user_auth, day_data, user_personalise_obj):
    today = datetime.date.today()
    user_plan = user_auth.user_plans.filter(is_active=True).last()
    if not user_plan:
        return None
    onboarding_date = user_plan.start_date

    if onboarding_date == today or not isinstance(day_data, ActualDay):
        if onboarding_date != today and not isinstance(day_data, ActualDay):
            logger.error(
                "User should have an ActualDay",
                extra=log_extra_fields(user_auth_id=user_auth.id),
            )

        current_prs = (
            user_personalise_obj.starting_prs
            if user_personalise_obj is not None
            else user_auth.personalise_data.filter(is_active=True).first().starting_prs
        )
    else:
        current_prs = day_data.prs_accuracy_score
    if current_prs < 0:
        current_prs = 0

    if current_prs is not None:
        return round(current_prs)


def get_previous_and_upcoming_rides(
    planned_sessions, user_local_date, upcoming_rides_count=3
):
    previous_rides = planned_sessions.filter(
        session_date_time__date__lt=user_local_date
    )
    upcoming_rides = planned_sessions.filter(
        session_date_time__date__gt=user_local_date
    )

    today_planned_sessions = planned_sessions.filter(
        session_date_time__date=user_local_date
    )
    today_completed_session_ids = [
        planned_session.id
        for planned_session in today_planned_sessions
        if planned_session.is_evaluation_done
    ]

    previous_rides |= today_planned_sessions.filter(id__in=today_completed_session_ids)
    upcoming_rides |= today_planned_sessions.exclude(id__in=today_completed_session_ids)

    previous_rides = previous_rides.order_by("-session_date_time")[:3]
    upcoming_rides = upcoming_rides.order_by("session_date_time")[:upcoming_rides_count]

    return previous_rides, upcoming_rides


def get_total_distance_covered_from_onboarding_day(user_auth):
    try:
        total_plan_distance = (
            ActualSession.objects.filter_actual_sessions(user_auth=user_auth).aggregate(
                Sum("actual_distance_in_meters")
            )["actual_distance_in_meters__sum"]
            or 0.0
        )

        return round((total_plan_distance / 1000), 1)  # Converting into kilometers
    except Exception as e:
        logger.exception(str(e) + "total_plan_distance not found")
        return 0


def is_day_completed(_date, user, event_date=None):
    """
    Day is completed if it is a recovery day or an actual session is already paired with today's planned session.
    If there isn't any planned session for this date then also return true. If it's event day then ignore the
    recovery day.
    """
    planned_session = PlannedSession.objects.filter(
        session_date_time__date=_date, user_auth=user, is_active=True
    ).last()
    if planned_session:
        return ActualSession.objects.filter(
            session_code=planned_session.session_code,
            is_active=True,
            third_party__isnull=False,
        ).exists() or (planned_session.is_recovery_session() and not event_date)
    return True
