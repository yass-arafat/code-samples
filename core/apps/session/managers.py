import logging
from datetime import timedelta

from django.db import models

from core.apps.common.const import TIME_RANGE_BOUNDARY

logger = logging.getLogger(__name__)


class ActualSessionManager(models.Manager):
    def filter_actual_sessions(self, user_auth, **extra_fields):
        actual_sessions = (
            self.filter(user_auth=user_auth, is_active=True, **extra_fields)
            .exclude(third_party__isnull=True)
            .select_related("third_party")
            .order_by("session_date_time", "third_party__priority")
        )

        picked_session_ids = []
        temp_picked_session = None
        activity_time = None
        for actual_session in actual_sessions:
            if activity_time is None:
                activity_time = actual_session.session_date_time
                temp_picked_session = actual_session
            else:
                if (
                    abs(
                        (
                            actual_session.session_date_time - activity_time
                        ).total_seconds()
                    )
                    <= 120
                ):
                    if (
                        actual_session.third_party.priority
                        < temp_picked_session.third_party.priority
                    ):
                        activity_time = actual_session.session_date_time
                        temp_picked_session = actual_session
                else:
                    picked_session_ids.append(temp_picked_session.id)
                    activity_time = actual_session.session_date_time
                    temp_picked_session = actual_session
        if temp_picked_session:
            picked_session_ids.append(temp_picked_session.id)

        return actual_sessions.filter(id__in=picked_session_ids)

    def filter_actual_sessions_with_time_range(
        self, user_auth, session_date_time, **extra_fields
    ):
        start_time = session_date_time - timedelta(seconds=TIME_RANGE_BOUNDARY)
        end_time = session_date_time + timedelta(seconds=TIME_RANGE_BOUNDARY)
        extra_fields.update(session_date_time__range=(start_time, end_time))
        return self.filter_actual_sessions(user_auth, **extra_fields).last()


class PlannedSessionManager(models.Manager):
    def filter_zone_difficulty_sessions(self, **extra_fields):
        return self.filter(session__difficulty_level__isnull=False, **extra_fields)
