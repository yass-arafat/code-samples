import datetime
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.messages import (
    WAHOO_DISCONNECT_NOTIFICATION_BODY,
    WAHOO_DISCONNECT_NOTIFICATION_TITLE,
    WAHOO_LINKED_NOTIFICATION_BODY,
    WAHOO_LINKED_NOTIFICATION_TITLE,
)
from core.apps.common.utils import (
    dakghor_connect_athlete,
    dakghor_disconnect_athlete,
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.data_provider.wahoo.api.versioned.v2.schema import (
    WahooConnectViewSchema,
    WahooDisconnectViewSchema,
)
from core.apps.data_provider.wahoo.services import UserWahooService
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.services import (
    create_notification,
    third_party_connect_notification,
    third_party_disconnect_notification,
)
from core.apps.user_profile.models import UserActivityLog
from core.apps.utp.utils import update_utp_settings

logger = logging.getLogger(__name__)


class WahooConnectView(APIView):
    @swagger_auto_schema(
        request_body=WahooConnectViewSchema.request_schema,
        responses=WahooConnectViewSchema.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        log_extra_data = log_extra_fields(
            user_auth_id=user.id,
            request_url=request.path,
            service_type=ServiceType.API.value,
        )
        source = ThirdPartySources.WAHOO.value[1].lower()

        logger.info("Connecting user to Wahoo", extra=log_extra_data)

        user_info = UserWahooService.get_wahoo_user_info(
            request.data.get("access_token")
        )

        wahoo_expire_at = UserWahooService.get_wahoo_expire_at(
            request.data.get("expires_in")
        )

        dakghor_response = dakghor_connect_athlete(
            athlete_id=user.id,
            source=source,
            user_id=str(user_info["id"]),
            user_token=request.data.get("access_token"),
            refresh_token=request.data.get("refresh_token"),
            expires_at=wahoo_expire_at,
            scope=request.data.get("scope"),
        )

        if dakghor_response.status_code != 200:
            logger.info(
                f"Status Code not 200 from Dakghor. Response message: {dakghor_response.json()['message']}",
                extra=log_extra_data,
            )
            return Response(dakghor_response.json())

        logger.info(
            "Successfully stored Wahoo credentials in Dakghor", extra=log_extra_data
        )

        update_utp_settings(
            user,
            True,
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
            datetime.datetime.now(),
            reason="wahoo connect",
        )

        third_party_connect_notification(user)
        response = make_context(
            error=False, message="Wahoo Connected Successfully", data=None
        )
        create_notification(
            user,
            NotificationTypeEnum.THIRD_PARTY_ACCOUNT_LINKED,
            WAHOO_LINKED_NOTIFICATION_TITLE,
            WAHOO_LINKED_NOTIFICATION_BODY,
        )

        UserActivityLog.objects.create(
            request=request.data,
            response=response,
            user_auth=user,
            user_id=user.code,
            activity_code=UserActivityLog.ActivityCode.WAHOO_CONNECT,
        )
        return Response(response)


class WahooDisconnectView(APIView):
    @swagger_auto_schema(responses=WahooDisconnectViewSchema.responses)
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        try:
            dakghor_response = dakghor_disconnect_athlete(
                source=ThirdPartySources.WAHOO.value[1].lower(), athlete_id=user.id
            )

            if dakghor_response.status_code != 200:
                logger.info(
                    f"Status Code not 200 from Dakghor. Response message: {dakghor_response.json()['message']}"
                )
                return Response(dakghor_response.json())

            update_utp_settings(
                user,
                False,
                USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
                datetime.datetime.now(),
                reason="wahoo disconnected",
            )
            third_party_disconnect_notification(user)

            create_notification(
                user,
                NotificationTypeEnum.THIRD_PARTY_PROFILE_DISCONNECTED,
                WAHOO_DISCONNECT_NOTIFICATION_TITLE,
                WAHOO_DISCONNECT_NOTIFICATION_BODY,
            )

            response = make_context(
                error=False,
                message="User pillar wahoo credentials deleted successfully",
                data=None,
            )

        except Exception as e:
            message = "Failed to disconnect wahoo credentials"
            logging.exception(
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
            activity_code=UserActivityLog.ActivityCode.WAHOO_DISCONNECT,
        )

        return Response(response)
