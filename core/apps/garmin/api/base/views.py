import datetime
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.messages import (
    GARMIN_DISCONNECT_NOTIFICATION_BODY,
    GARMIN_DISCONNECT_NOTIFICATION_TITLE,
    GARMIN_LINKED_NOTIFICATION_BODY,
    GARMIN_LINKED_NOTIFICATION_TITLE,
)
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    dakghor_backfill_request,
    dakghor_connect_athlete,
    dakghor_disconnect_athlete,
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.services import (
    create_notification,
    third_party_connect_notification,
    third_party_disconnect_notification,
)
from core.apps.user_profile.models import UserActivityLog
from core.apps.utp.utils import update_utp_settings

from ...services import UserGarminService
from .schema import SendPillarWorkoutToGarminV1SchemaView

logger = logging.getLogger(__name__)


@api_view(["POST"])
def garmin_connect(request):
    user = get_user_from_session_destroy_session_variable(request)
    log_extra_data = log_extra_fields(
        user_auth_id=user.id,
        request_url=request.path,
        service_type=ServiceType.API.value,
    )

    source = ThirdPartySources.GARMIN.value[1].lower()

    logger.info("Connecting user to Garmin", extra=log_extra_data)
    dakghor_response = dakghor_connect_athlete(
        athlete_id=user.id,
        source=source,
        user_id=request.data.get("garmin_user_id"),
        user_token=request.data.get("garmin_user_token"),
        user_secret=request.data.get("garmin_user_secret"),
    )
    if dakghor_response.status_code != 200:
        logger.info(
            f"Status Code not 200 from Dakghor. Response message: {dakghor_response.json()['message']}",
            extra=log_extra_data,
        )
        return Response(dakghor_response.json())

    if user.user_plans.exists():
        logger.info("Running backfill", extra=log_extra_data)
        dakghor_backfill_request(source=source, athlete_id=user.id)

    logger.info(
        "Successfully stored Garmin credentials in Dakghor", extra=log_extra_data
    )
    update_utp_settings(
        user,
        True,
        USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
        datetime.datetime.now(),
        reason="garmin connect",
    )
    third_party_connect_notification(user)
    response = make_context(
        error=False, message="Garmin Connected Successfully", data=None
    )
    create_notification(
        user,
        NotificationTypeEnum.THIRD_PARTY_ACCOUNT_LINKED,
        GARMIN_LINKED_NOTIFICATION_TITLE,
        GARMIN_LINKED_NOTIFICATION_BODY,
    )

    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        user_auth=user,
        user_id=user.code,
        activity_code=UserActivityLog.ActivityCode.GARMIN_CONNECT,
    )
    return Response(response)


@api_view(["GET"])
def garmin_disconnect(request):
    user = get_user_from_session_destroy_session_variable(request)
    try:
        dakghor_disconnect_athlete(
            source=ThirdPartySources.GARMIN.value[1].lower(), athlete_id=user.id
        )
        update_utp_settings(
            user,
            False,
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
            datetime.datetime.now(),
            reason="garmin disconnect",
        )
        third_party_disconnect_notification(user)
        create_notification(
            user,
            NotificationTypeEnum.THIRD_PARTY_PROFILE_DISCONNECTED,
            GARMIN_DISCONNECT_NOTIFICATION_TITLE,
            GARMIN_DISCONNECT_NOTIFICATION_BODY,
        )

        response = make_context(
            error=False,
            message="User pillar garmin credentials deleted successfully",
            data=None,
        )
    except Exception as e:
        message = "Failed to disconnect garmin credentials"
        logger.exception(
            message,
            extra=log_extra_fields(
                user_auth_id=user.id,
                exception_message=str(e),
                service_type=ServiceType.API.value,
                request_url=request.path,
            ),
        )
        response = make_context(error=True, message=message, data=None)

    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        user_auth=user,
        user_id=user.code,
        activity_code=UserActivityLog.ActivityCode.GARMIN_DISCONNECT,
    )
    return Response(response)


class SendPillarWorkoutToGarminV1(APIView):
    """Sends Pillar workouts prepared for users to Garmin Connect"""

    activity_code = UserActivityLog.ActivityCode.SEND_WORKOUT_TO_GARMIN

    @swagger_auto_schema(
        request_body=SendPillarWorkoutToGarminV1SchemaView.request_schema,
        responses=SendPillarWorkoutToGarminV1SchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        workout_name = request.data.get("workout_name", False)
        data_type = request.data.get("data_type", False)
        ftp = request.data.get("ftp", False)
        fthr = request.data.get("fthr", False)
        planned_id = request.data.get("session_metadata")["planned_id"]

        try:
            error, message, data = UserGarminService.send_pillar_workout_to_garmin(
                user, workout_name, data_type, ftp, fthr, planned_id
            )
            response = make_context(error, message, data)

        except Exception as e:
            logger.exception(
                "Could not send workout to Garmin.",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    request_url=request.path,
                    exception_message=str(e),
                ),
            )
            response = make_context(True, "Could not send workout to Garmin", None)

        return PillarResponse(user, request, response, self.activity_code)
