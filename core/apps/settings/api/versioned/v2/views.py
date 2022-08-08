import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import (
    clear_user_cache,
    clear_user_cache_with_prefix,
)
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import log_extra_fields, make_context
from core.apps.notification.services import PushNotificationSettingService
from core.apps.settings.api.versioned.v2.schema import (
    UserInfoSchemaView,
    UserInitSettingsSchemaView,
    UserResetSettingsSchemaView,
)
from core.apps.settings.api.versioned.v2.services import SettingsService
from core.apps.settings.utils import get_access_level
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.models import UserActivityLog

logger = logging.getLogger(__name__)


class UserInitSettingsView(APIView):
    """Sets initial settings when user register"""

    success_msg = "User initial settings saved successfully"
    error_msg = "Could not save user's initial settings"

    @swagger_auto_schema(
        request_body=UserInitSettingsSchemaView.request_schema,
        responses=UserInitSettingsSchemaView.responses,
    )
    def post(self, request):
        code = request.data.get("code")

        logger.info(f"Creating user in user auth table code = {code}")
        user = UserAuthModel.objects.create(code=code, is_active=True)

        logger.info(
            f"Created user Id = {user.id} code = {user.code}. Now saving settings...."
        )
        try:
            SettingsService.save_user_initial_settings(user_id=code)
            data = {"access_level": get_access_level(user_id=code)}
            error, msg, status = False, self.success_msg, 200

        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    request_url=request.path,
                    service_type=ServiceType.API.value,
                    exception_message=str(e),
                ),
            )
            error, msg, data, status = True, self.error_msg, None, 500

        UserActivityLog.objects.create(
            request=request.data,
            response=make_context(error, msg, None),
            activity_code=UserActivityLog.ActivityCode.USER_REGISTRATION,
            user_id=code,
        )

        return Response(make_context(error, msg, data), status=status)


class UserResetSettingsView(APIView):
    """Remove settings when user logs out"""

    success_msg = "User settings reset successfully"
    error_msg = "Could not reset user's initial settings"

    @swagger_auto_schema(
        request_body=UserResetSettingsSchemaView.request_schema,
        responses=UserResetSettingsSchemaView.responses,
    )
    def post(self, request):
        code = request.data.get("code")
        fcm_device_token = request.data.get("fcm_device_token")

        try:
            user = UserAuthModel.objects.filter(code=code, is_active=True).last()
            PushNotificationSettingService(
                user_auth=user, user_id=code
            ).delete_push_notification_setting(device_token=fcm_device_token)
            clear_user_cache_with_prefix(prefix=code, user_id=code)
            error, msg, status = False, self.success_msg, 200
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    request_url=request.path,
                    service_type=ServiceType.API.value,
                    exception_message=str(e),
                ),
            )
            error, msg, status = True, self.error_msg, 500

        UserActivityLog.objects.create(
            request=request.data,
            response=make_context(error=error, message=msg, data=None),
            activity_code=UserActivityLog.ActivityCode.USER_LOGOUT,
            user_id=code,
        )

        return Response(make_context(error, msg, None), status=status)


class UserInfoView(APIView):
    """Sets initial settings when user register"""

    success_msg = "User info returned successfully"
    error_msg = "Could not return user info"

    @swagger_auto_schema(
        request_body=UserInfoSchemaView.request_schema,
        responses=UserInfoSchemaView.responses,
    )
    def post(self, request):
        code = request.data.get("code")
        try:

            error, msg, data, status = (
                False,
                self.success_msg,
                {"access_level": get_access_level(user_id=code)},
                200,
            )
            clear_user_cache(user_id=code)

        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    request_url=request.path,
                    service_type=ServiceType.API.value,
                    exception_message=str(e),
                ),
            )
            error, msg, data, status = True, self.error_msg, None, 500

        UserActivityLog.objects.create(
            request=request.data,
            response=make_context(error=error, message=msg, data=data),
            activity_code=UserActivityLog.ActivityCode.EMAIL_LOGIN,
            user_id=code,
        )

        return Response(make_context(error, msg, data), status=status)
