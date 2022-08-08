import logging
from datetime import date, timedelta

import requests
from django.conf import settings
from django.db import connections
from django.db.models import Count, Max
from django_rq import job

from core.apps.common.const import (
    IMPORTANT_TIMEZONES,
    LOAD_CHANGE_LIMIT,
    SQS_CHANGE_LIMIT,
)
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.session.models import PlannedSession

logger = logging.getLogger(__name__)


@job
def load_sqs_change_check():
    """Will check for unusual changes in load and SQS of users"""
    try:
        today = date.today()
        yesterday = str(today - timedelta(days=1))
        today = str(today)

        schema_name = settings.DATABASE_SCHEMA_NAME

        raw_query = (
            f"WITH y_date AS (SELECT user_auth_id, actual_load, sqs_today FROM {str(schema_name)}.actual_day "
            f"WHERE activity_date = '{yesterday}' AND is_active = true), "
            f"t_date AS (SELECT user_auth_id, actual_load, sqs_today "
            f"FROM {str(schema_name)}.actual_day WHERE activity_date = '{today}' AND is_active = true) "
            f"SELECT y_date.user_auth_id FROM y_date JOIN t_date ON y_date.user_auth_id = t_date.user_auth_id "
            f"WHERE y_date.actual_load - t_date.actual_load > {LOAD_CHANGE_LIMIT} "
            f"OR y_date.sqs_today - t_date.sqs_today > {SQS_CHANGE_LIMIT}"
        )

        cursor = connections["default"].cursor()
        cursor.execute(raw_query)
        temp_user_set = set(cursor.fetchall())

        raw_query = (
            f"SELECT user_auth_id FROM {str(schema_name)}.user_profile "
            f"WHERE timezone_id IN {IMPORTANT_TIMEZONES} AND is_active = true"
        )

        cursor.execute(raw_query)
        required_user_set = set(cursor.fetchall())

        flagged_user_list = list(temp_user_set.intersection(required_user_set))
        if flagged_user_list:
            message = (
                f"Actual load or SQS changed more than change limit for {[user for user in flagged_user_list]} "
                f"at {today} when running load and SQS change check cron."
            )
            logger.error(message)
    except Exception as e:
        logger.exception(f"Unusual load and SQS change check failed. Exception: {e}")
        requests.post(
            url=settings.ASYNC_HEALTHCHECK_URL + "/fail",
            data={"Exception": e, "Cron": "Unusual Load and SQS change check"},
        )


def duplicate_day_session_check():
    """
    Will check for duplicate activated rows in Actual Day, Planned Day
    and Planned Session tables and fix them if found.
    """

    # Check and fix duplicate Actual Days
    duplicate_actual_days = (
        ActualDay.objects.filter(is_active=True)
        .values("user_auth_id", "activity_date")
        .annotate(count=Count("activity_date"))
        .filter(count__gt=1)
    )

    activity_dates = [
        actual_day["activity_date"] for actual_day in duplicate_actual_days
    ]
    affected_users = [
        actual_day["user_auth_id"] for actual_day in duplicate_actual_days
    ]

    # Get the last created objects for the affected days. These are the objects that
    # should be remain true for those activity days (in the above activity_dates list.
    # All other objects of those activity days should remain false.
    latest_actual_days = (
        ActualDay.objects.filter(
            is_active=True,
            activity_date__in=activity_dates,
            user_auth_id__in=affected_users,
        )
        .values("user_auth_id", "activity_date")
        .annotate(max_id=Max("id"))
    )
    # Get the ids of latest_actual_days
    max_ids = [actual_day["max_id"] for actual_day in latest_actual_days]

    # By following query, we will get the duplicate active day objects which should have
    # been deactivated
    duplicate_actual_days = ActualDay.objects.filter(
        is_active=True,
        activity_date__in=activity_dates,
        user_auth_id__in=affected_users,
    ).exclude(id__in=max_ids)

    if duplicate_actual_days:
        # if duplicate days found, get the ids of these duplicate objects so that we can
        # print these ids for later investigating why they were created
        duplicate_actual_day_ids = duplicate_actual_days.values_list("id").order_by(
            "id"
        )

        # Finally, deactivate the duplicate active days
        duplicate_actual_days.update(is_active=False)
        logger.exception(
            f"Duplicate Actual Days found and fixed. "
            f"Duplicate ids: {[day_id for day_id in duplicate_actual_day_ids]}"
        )

    # Check and fix duplicate Planned Days
    duplicate_planned_days = (
        PlannedDay.objects.filter(is_active=True)
        .values("user_auth_id", "activity_date")
        .annotate(count=Count("activity_date"))
        .filter(count__gt=1)
    )

    activity_dates = [
        planned_day["activity_date"] for planned_day in duplicate_planned_days
    ]
    affected_users = [
        planned_day["user_auth_id"] for planned_day in duplicate_planned_days
    ]
    latest_planned_days = (
        PlannedDay.objects.filter(
            is_active=True,
            activity_date__in=activity_dates,
            user_auth_id__in=affected_users,
        )
        .values("user_auth_id", "activity_date")
        .annotate(max_id=Max("id"))
    )
    max_ids = [planned_day["max_id"] for planned_day in latest_planned_days]

    duplicate_planned_days = PlannedDay.objects.filter(
        is_active=True,
        activity_date__in=activity_dates,
        user_auth_id__in=affected_users,
    ).exclude(id__in=max_ids)

    if duplicate_planned_days:
        duplicate_planned_day_ids = duplicate_planned_days.values_list("id").order_by(
            "id"
        )
        duplicate_planned_days.update(is_active=False)
        logger.exception(
            f"Duplicate Actual Days found and fixed. "
            f"Duplicate ids: {duplicate_planned_day_ids}"
        )

    # Check and fix duplicate Planned Sessions
    duplicate_planned_sessions = (
        PlannedSession.objects.filter(is_active=True)
        .values("user_auth_id", "session_date_time")
        .annotate(count=Count("session_date_time"))
        .filter(count__gt=1)
    )

    session_date_times = [
        planned_session["session_date_time"]
        for planned_session in duplicate_planned_sessions
    ]
    affected_users = [
        planned_session["user_auth_id"]
        for planned_session in duplicate_planned_sessions
    ]
    latest_planned_sessions = (
        PlannedSession.objects.filter(
            is_active=True,
            session_date_time__in=session_date_times,
            user_auth_id__in=affected_users,
        )
        .values("user_auth_id", "session_date_time")
        .annotate(max_id=Max("id"))
    )
    max_ids = [planned_session["max_id"] for planned_session in latest_planned_sessions]

    duplicate_planned_sessions = PlannedSession.objects.filter(
        is_active=True,
        session_date_time__in=session_date_times,
        user_auth_id__in=affected_users,
    ).exclude(id__in=max_ids)

    if duplicate_planned_sessions:
        duplicate_planned_session_ids = duplicate_planned_sessions.values_list(
            "id"
        ).order_by("id")
        duplicate_planned_sessions.update(is_active=False)
        logger.exception(
            f"Duplicate Actual Days found and fixed. "
            f"Duplicate ids: {duplicate_planned_session_ids}"
        )
