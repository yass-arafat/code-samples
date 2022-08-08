import logging

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import pillar_response
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user,
    get_user_from_session_destroy_session_variable,
    get_user_metadata,
    log_extra_fields,
    make_context,
    update_user_metadata_cache,
)
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.models import UserActivityLog

from ...enums.notification_type_enum import NotificationTypeEnum
from ...models import PushNotificationLog
from ...services import (
    DeactivateInAppNotificationService,
    InAppNotificationSevice,
    NotificationPanelService,
    NotificationService,
    PushNotificationService,
    PushNotificationSettingService,
    create_notification,
    get_user_notification,
    get_user_notification_list,
    update_user_notification,
)
from .serializers import UserNotificationSerializer

logger = logging.getLogger(__name__)


class NotificationView(APIView):
    # Create Notifications
    def post(self, request):
        logger.info(f"Got request to send notifications {request.data}")

        user_code = request.data.get("user_code")
        payment = request.data.get("payment", None)
        notification_type_enum_code = request.data.get("notification_type_enum_code")
        notification_title = request.data.get("notification_title")
        notification_message = request.data.get("notification_message")
        data = request.data.get("data")
        try:
            user_auth = UserAuthModel.objects.filter(
                is_active=True, code=user_code
            ).last()
            create_notification(
                user_auth=user_auth,
                notification_type_enum=NotificationTypeEnum.get_notification_type_enum_from_code(
                    notification_type_enum_code
                ),
                notification_title=notification_title,
                notification_message=notification_message,
                data=data,
                payment=payment,
            )
            error, msg, data = False, "Created notifications successfully", None
        except Exception as e:
            logger.info(f" Exception occurs = {e}")
            error, msg, data = (
                True,
                "Unable to create notifications, Please check server log",
                None,
            )

        return Response(make_context(error=error, message=msg, data=data))


class UserNotificationView(generics.GenericAPIView):
    serializer_class = UserNotificationSerializer

    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        error, msg, data = get_user_notification(user)

        return Response(make_context(error, msg, data))

    def post(self, request, notification_id):
        user = get_user_from_session_destroy_session_variable(request)
        error, msg, data = update_user_notification(user, notification_id, request)

        return Response(make_context(error, msg, data))


class SyncView(APIView):
    activity_code = UserActivityLog.ActivityCode.SYNC_INIT

    @pillar_response(activity_code)
    def post(self, request):
        """Sync user actions view"""

        user_id = request.session["user_id"]

        # try:
        #     user_actions = sync_user_actions(user)
        # except Exception as e:
        #     logger.error(f"Could not sync user actions. Exception: {str(e)}")
        user_actions = []

        user_metadata = get_user_metadata(user_id)

        if user_metadata:
            logger.info(f"found user meta data for {user_id}")
            user_metadata_hash = user_metadata.hash
            response = dict(
                user_metadata_hash=user_metadata_hash,
                actions=user_actions,
                cache_id=user_metadata.cache_id,
            )
        else:
            response = dict(
                user_metadata_hash=None,
                actions=user_actions,
                cache_id=0,
            )
        return response


class SyncUpdateView(APIView):
    @pillar_response()
    def post(self, request):
        user_id_list = request.data.get("user_id_list", [])
        update_user_metadata_cache(user_id_list)


class PushNotificationAcknowledgeView(APIView):
    def post(self, request, push_notification_id):
        """Push notification acknowledgement view"""

        user = get_user_from_session_destroy_session_variable(request)

        try:
            user_push_notification = PushNotificationLog.objects.get(
                user_auth=user, id=push_notification_id
            )
        except PushNotificationLog.DoesNotExist:
            error, msg, data = True, "No notification found with the id", None
        else:
            user_push_notification.notification_status = (
                PushNotificationLog.NotificationStatus.ACKNOWLEDGED
            )
            user_push_notification.save(
                update_fields=["notification_status", "updated_at"]
            )

            error, msg, data = False, "", None

        return Response(make_context(error, msg, data))


class PushNotificationView(APIView):
    def post(self, request):
        """Push notification view"""

        user_id = request.session["user_id"]
        try:
            user_auth = UserAuthModel.objects.filter(code=user_id).last()
            PushNotificationService(
                user_auth
            ).send_push_notification_from_other_service(request)
            response = make_context(False, "Successfully sent push notification", None)
        except Exception as e:
            message = "Failed to send push notification"
            logger.exception(
                "Failed to send push notification",
                extra=log_extra_fields(
                    request_url=request.path,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    user_id=user_id,
                ),
            )
            response = make_context(True, message, None)
        return Response(response)


class NewNotificationView(APIView):
    def post(self, request):
        """Notification view"""

        user_id = request.session["user_id"]
        try:
            NotificationService(user_id).create_notification(request)
            response = make_context(False, "Successfully created notification", None)
        except Exception as e:
            message = "Failed to send push notification"
            logger.exception(
                "Failed to send push notification",
                extra=log_extra_fields(
                    request_url=request.path,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    user_id=user_id,
                ),
            )
            response = make_context(True, message, None)
        return Response(response)


class DeviceTokenView(APIView):
    def post(self, request):
        """Store or update user device token"""

        user_id = request.session["user_id"]
        user_auth = UserAuthModel.objects.filter(code=user_id).last()

        old_token = request.data.get("old_token", None)
        new_token = request.data.get("new_token", None)
        token_type = request.data.get("token_type", "").lower()

        PushNotificationSettingService(
            user_auth=user_auth, user_id=user_id
        ).update_push_notification_setting(token_type, old_token, new_token)

        error, msg, data = False, "Device token saved successfully", None
        return Response(make_context(error, msg, data))


class NotificationListView(APIView):
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        last_id = int(request.GET.get("last_id", 0))

        try:
            notification_list = get_user_notification_list(user, last_id)
            response = make_context(
                False, "Notification list returned successfully", notification_list
            )
            status_code = status.HTTP_200_OK
        except Exception as e:
            logger.exception(
                f"Failed to return notification list where previous page "
                f"last notification id: {last_id}",
                extra=log_extra_fields(
                    service_type=ServiceType.API.value,
                    exception_message=str(e),
                    user_id=user.code,
                    user_auth_id=user.id,
                    request_url=request.path,
                ),
            )
            response = make_context(True, "Could not return notification list", None)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(response, status=status_code)


class InAppNotificationView(APIView):
    @pillar_response()
    def get(self, request):
        """get all in app notification list"""
        notification_data = InAppNotificationSevice(request).get_notification_list()
        return notification_data

    @pillar_response()
    def post(self, request):
        """create new in app notification"""
        return InAppNotificationSevice(request).create_notification()

    @pillar_response()
    def patch(self, request):
        """update in app notification action"""
        InAppNotificationSevice(request).update_notification()

    @pillar_response()
    def delete(self, request):
        """deactivate in app notification"""
        InAppNotificationSevice(request).deactivate_notification()


class NotificationPanelView(APIView):
    @pillar_response()
    def get(self, request):
        """get notification data"""
        panel_data = NotificationPanelService(
            user_id=get_user(request=request)
        ).get_notification_panel_data()
        return panel_data


class DeactivateInAppNotificationView(APIView):
    @pillar_response()
    def post(self, request):
        """deactivate in app notification"""
        data = DeactivateInAppNotificationService(request).deactivate_notification()
        return data
