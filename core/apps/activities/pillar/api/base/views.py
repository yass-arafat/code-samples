import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import clear_user_cache
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.user_profile.models import UserActivityLog

from ...services import ManualActivityService
from ...tasks import process_athlete_activity_from_dakghor

logger = logging.getLogger(__name__)


class ManualActivityView(APIView):
    """Records the manual activity created by user from Pillar app"""

    activity_code = UserActivityLog.ActivityCode.ADD_MANUAL_ACTIVITY

    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        try:
            input_obj = ManualActivityService.get_manual_activity_input(request, user)
            error, msg, data = ManualActivityService.record_manual_activity(
                user, input_obj
            )
            clear_user_cache(user)

            response = make_context(error=error, message=msg, data=data)
            UserActivityLog.objects.create(
                request=request.data,
                response=response,
                user_auth=user,
                user_id=user.code,
                activity_code=self.activity_code,
            )
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Couldn't save manual activity. Exception: {str(e)}.")
            data = f"{str(e)}"
            msg = "Couldn't save manual activity"
            UserActivityLog.objects.create(
                request=request.data,
                data=data,
                user_auth=user,
                user_id=user.code,
                activity_code=self.activity_code,
            )
            return Response(
                make_context(True, msg, None),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ThirdPartyActivityView(APIView):
    def post(self, request):
        logger.info(f"Received activity data from dakghor {request.data}")

        athletes = request.data.get("athletes")
        try:
            for athlete in athletes:
                athlete_id = athlete["id"]
                activities = athlete["activities"]
                logger.info(f"athlete id {athlete_id} and activities {activities}")
                process_athlete_activity_from_dakghor.delay(athlete_id, activities)
            logger.info("Activity data are successfully processed")
        except Exception as e:
            logger.exception(
                "Failed to calculate activity data in core.",
                extra=log_extra_fields(
                    request_url=request.path,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                ),
            )
            return Response(
                make_context(True, "Failed to calculate activity data in core.", None)
            )

        return Response(
            make_context(False, "Successfully received third party activities", None)
        )
