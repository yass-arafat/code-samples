import logging
from datetime import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.messages import (
    STRAVA_DISCONNECT_NOTIFICATION_BODY,
    STRAVA_DISCONNECT_NOTIFICATION_TITLE,
    STRAVA_LINKED_NOTIFICATION_BODY,
    STRAVA_LINKED_NOTIFICATION_TITLE,
)
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
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

from ...services import StravaService

logger = logging.getLogger(__name__)


@api_view(["POST"])
def connect_strava(request):
    activity_code = UserActivityLog.ActivityCode.STRAVA_CONNECT
    user_auth = get_user_from_session_destroy_session_variable(request)
    log_extra_data = log_extra_fields(
        user_auth_id=user_auth.id,
        request_url=request.path,
        service_type=ServiceType.API.value,
    )

    source = ThirdPartySources.STRAVA.value[1].lower()
    logger.info("Connecting user to Strava", extra=log_extra_data)
    dakghor_response = dakghor_connect_athlete(
        athlete_id=user_auth.id,
        source=source,
        user_id=request.data.get("strava_user_id"),
        user_token=request.data.get("strava_user_token"),
        user_name=request.data.get("strava_user_name", None),
        refresh_token=request.data.get("strava_refresh_token"),
        expires_at=request.data.get("strava_token_expires_at"),
        scope=request.data.get("strava_scope"),
    )
    if dakghor_response.status_code != 200:
        return PillarResponse(
            user_auth, request, dakghor_response.json(), activity_code
        )

    # if user_auth.user_plans.exists():
    #     logger.info("Running backfill", extra=log_extra_data)
    #     dakghor_backfill_request(source=source, athlete_id=user_auth.id)

    logger.info(
        "Successfully stored Strava credentials in Dakghor", extra=log_extra_data
    )
    update_utp_settings(
        user_auth,
        True,
        USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
        datetime.now(),
        reason="strava connect",
    )
    third_party_connect_notification(user_auth)
    response = make_context(
        error=False, message="Strava Connected Successfully", data=None
    )
    create_notification(
        user_auth,
        NotificationTypeEnum.THIRD_PARTY_ACCOUNT_LINKED,
        STRAVA_LINKED_NOTIFICATION_TITLE,
        STRAVA_LINKED_NOTIFICATION_BODY,
    )

    return PillarResponse(user_auth, request, response, activity_code)


@api_view(["GET"])
def disconnect_strava(request):
    user_auth = get_user_from_session_destroy_session_variable(request)
    err, msg = StravaService.delete_strava_credentials(user=user_auth)

    if not err:
        dakghor_disconnect_athlete(
            ThirdPartySources.STRAVA.value[1].lower(), user_auth.id
        )
        update_utp_settings(
            user_auth,
            False,
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
            datetime.now(),
            reason="strava disconnect",
        )
        third_party_disconnect_notification(user_auth)
        create_notification(
            user_auth,
            NotificationTypeEnum.THIRD_PARTY_PROFILE_DISCONNECTED,
            STRAVA_DISCONNECT_NOTIFICATION_TITLE,
            STRAVA_DISCONNECT_NOTIFICATION_BODY,
        )

    response = make_context(error=err, message=msg, data=None)

    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        user_auth=user_auth,
        user_id=user_auth.code,
        activity_code=UserActivityLog.ActivityCode.STRAVA_DISCONNECT,
    )

    return Response(response)
