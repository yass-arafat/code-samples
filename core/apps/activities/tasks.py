import logging

from core.apps.common.date_time_utils import convert_str_date_to_date_obj, daterange
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import log_extra_fields
from core.apps.session.models import ActualSession
from core.apps.user_auth.models import UserAuthModel

from .utils import recalculate_single_day

logger = logging.getLogger(__name__)


# @shared_task
def recalculate_data_for_daterange(user_auth_id, start_date, end_date):
    try:
        start_date = convert_str_date_to_date_obj(start_date)
        end_date = convert_str_date_to_date_obj(end_date)
        user_auth = UserAuthModel.objects.filter(pk=user_auth_id).first()
        actual_sessions = ActualSession.objects.filter_actual_sessions(
            user_auth=user_auth, session_date_time__date__range=(start_date, end_date)
        )
        for _date in daterange(start_date, end_date):
            recalculate_single_day(user_auth, actual_sessions, _date)
    except Exception as e:
        extra_log_fields = log_extra_fields(
            user_auth_id=user_auth_id,
            service_type=ServiceType.INTERNAL.value,
            exception_message=str(e),
        )
        logger.exception(
            f"Failed to recalculate session from {str(start_date)} to {str(end_date)}",
            extra=extra_log_fields,
        )
