import logging

from django.db import models
from django.db.models import F, Func

from core.apps.common.date_time_utils import convert_timezone_offset_to_seconds

logger = logging.getLogger(__name__)


class TimeZoneManager(models.Manager):
    def get_closest_timezone(self, offset):
        offset_second = convert_timezone_offset_to_seconds(offset)

        return (
            self.annotate(
                abs_diff=Func(F("offset_second") - offset_second, function="ABS")
            )
            .order_by("abs_diff")
            .first()
        )
