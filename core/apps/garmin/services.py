import logging

from rest_framework import status

from core.apps.common.messages import GARMIN_WORKOUT_HELPER_VIDEO_URL
from core.apps.common.utils import log_extra_fields
from core.apps.session.models import PlannedSession
from core.apps.user_profile.utils import update_user_threshold_value

from .utils import (
    get_json_format_workout_for_garmin,
    make_send_workout_to_garmin_request,
)

logger = logging.getLogger(__name__)


class UserGarminService:
    @staticmethod
    def send_pillar_workout_to_garmin(
        user, workout_name, data_type, ftp, fthr, planned_id
    ):
        planned_session = PlannedSession.objects.filter(
            user_auth=user, pk=planned_id, is_active=True
        ).last()
        if not planned_session:
            exception_message = (
                f"Planned session with session code {str(planned_id)} not found."
            )
            error_message = "Could not found planned session"
            extra_log_fields = log_extra_fields(
                user_auth_id=user.id, exception_message=exception_message
            )
            logger.exception(error_message, extra=extra_log_fields)
            return True, error_message, None

        update_user_threshold_value(user, data_type, ftp, fthr)
        formatted_workout = get_json_format_workout_for_garmin(
            workout_name, data_type, ftp, fthr, planned_session
        )
        response_code, msg = make_send_workout_to_garmin_request(
            user, formatted_workout
        )
        if response_code == status.HTTP_200_OK:
            logger.info(
                f"Pillar workout sent to Garmin successfully. Planned session ID: {planned_id}",
                extra=log_extra_fields(user_auth_id=user.id),
            )
            return (
                False,
                "Pillar workout sent to Garmin successfully",
                {"url": GARMIN_WORKOUT_HELPER_VIDEO_URL},
            )
        else:
            logger.info(
                f"Could not send Pillar workout to Garmin. Planned session ID: {planned_id}",
                extra=log_extra_fields(user_auth_id=user.id, exception_message=msg),
            )
            return True, "Could not send Pillar workout to Garmin", None
