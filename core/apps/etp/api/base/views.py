import logging
from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import pro_feature
from core.apps.common.date_time_utils import convert_str_date_time_to_date_time_obj
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.user_profile.models import UserActivityLog

from ...tasks import edit_training_plan

logger = logging.getLogger(__name__)


class EditGoalApiView(APIView):
    etp_activity_code = UserActivityLog.ActivityCode.EDIT_GOAL
    no_user_found_msg = "No user found with the access token"
    success_msg = "Updated goal date and training plan successfully"
    invalid_date_msg = "Selected event date cannot be past date"

    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        new_event_date = request.data.get("selected_event_date")
        if not user:
            return Response(make_context(True, self.no_user_found_msg, None))

        current_plan = user.user_plans.filter(is_active=True).last()
        if current_plan.user_package_id:
            response = make_context(True, "Package end date can not be changed.", None)
            return PillarResponse(
                user,
                request,
                response,
                self.etp_activity_code,
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_event_date_from_string = convert_str_date_time_to_date_time_obj(
            new_event_date
        ).date()
        if new_event_date_from_string < datetime.today().date():
            return PillarResponse(
                user,
                request,
                make_context(True, self.invalid_date_msg, None),
                self.etp_activity_code,
            )
        try:
            edit_training_plan(user.id, new_event_date_from_string)
        except Exception as e:
            logger.exception(
                "Failed to change event date",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
        return PillarResponse(
            user,
            request,
            make_context(False, self.success_msg, None),
            self.etp_activity_code,
        )
