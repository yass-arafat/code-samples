import logging

from django.db import models

from core.apps.common.utils import get_freshness

logger = logging.getLogger(__name__)


class ActualDayManager(models.Manager):
    def get_actual_freshness(self, user_auth, user_local_date):
        return (
            self.filter(
                user_auth=user_auth,
                activity_date=user_local_date,
                is_active=True,
            )
            .values("actual_freshness")
            .last()
            .get("actual_freshness")
        )


class PlannedDayManager(models.Manager):
    def get_planned_freshness(self, user_auth, activity_date):
        planned_day = (
            self.filter(
                user_auth=user_auth,
                activity_date=activity_date,
                is_active=True,
            )
            .values("planned_load", "planned_acute_load")
            .last()
        )

        if not planned_day:
            return
        return get_freshness(
            planned_day["planned_load"], planned_day["planned_acute_load"]
        )
