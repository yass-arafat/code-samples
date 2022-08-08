import logging

from django.conf import settings
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.activities.pillar.services import ManualActivityService
from core.apps.common.common_functions import (
    clear_cache_with_key,
    clear_user_cache,
    pro_feature,
)
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
    update_is_active_value,
)
from core.apps.evaluation.session_evaluation.utils import get_actual_session
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.models import Notification
from core.apps.plan.enums.session_status_enum import SessionStatusEnum
from core.apps.user_profile.models import UserActivityLog

from ...api.base.serializers import SessionRequestSerializer, SessionResponseSerializer
from ...dictionary import USER_AWAY_REASONS
from ...models import ActualSession, change_status, get_session_from_session_date
from ...services import (
    SessionPairingService,
    SessionService,
    UserAwayDeleteService,
    UserAwayService,
)
from ...utils import (
    delete_planned_session,
    move_planned_session,
    update_achievement_data,
)
from ..versioned.v2.services import SessionDetailService as SessionDetailServiceV2

logger = logging.getLogger(__name__)


class SessionGetView(generics.GenericAPIView):
    serializer_class = SessionRequestSerializer

    def get(self):
        pass

    def post(self, request):
        session_date = request.data["date"]
        plan_id = request.data["plan_id"]

        sessions = get_session_from_session_date(session_date, plan_id)
        if sessions is None:
            return Response(make_context(False, "No session Found", None))
        else:
            serialized = SessionResponseSerializer(sessions, many=True)
            return Response(
                make_context(
                    False, "Session data returned successfully", serialized.data
                )
            )


@api_view(["POST"])
def change_session_status(request):
    status = request.data["status"]
    session_id = request.data["session_id"]
    response = change_status(session_id, status)
    if response is None:
        return Response(
            make_context(
                True, "Couldn't Update the session status. Check Server log", None
            )
        )
    else:
        return Response(
            make_context(False, "Session status updated successfully", None)
        )


@api_view(["POST"])
def move_session(request):
    user = get_user_from_session_destroy_session_variable(request)

    try:
        error, message, data = move_planned_session(request, user)
        clear_user_cache(user)
    except Exception as e:
        error, message, data = True, "Session move failed", None
        logger.error(f"{message} Exception: {str(e)}")

    response = make_context(error, message, data)
    activity_code = UserActivityLog.ActivityCode.USER_SESSION_MOVE
    return PillarResponse(user, request, response, activity_code)


@api_view(["POST"])
def delete_session(request):
    user = get_user_from_session_destroy_session_variable(request)

    try:
        error, message, data = delete_planned_session(request, user)
        clear_user_cache(user)
    except Exception as e:
        error, message, data = True, "Session deletion failed", None
        logger.error(f"{message} Exception: {str(e)}")

    response = make_context(error, message, data)
    activity_code = UserActivityLog.ActivityCode.USER_SESSION_DELETE
    return PillarResponse(user, request, response, activity_code)


class UserAwayApiView(APIView):
    @pro_feature
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        if not user:
            return Response(
                make_context(True, "No user found with the access token", None),
                status=status.HTTP_401_UNAUTHORIZED,
            )
        data = {"reasons": USER_AWAY_REASONS}
        return Response(
            make_context(False, "I am away reasons returned successfully", data),
            status=status.HTTP_200_OK,
        )

    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        away_start_date = request.data["start_date"]
        away_end_date = request.data["end_date"]
        away_reason = request.data["reason"]

        user_away_service = UserAwayService(user, away_start_date, away_end_date)
        valid_input, msg = user_away_service.is_valid_input()

        if not valid_input:
            return Response(
                make_context(True, msg, None), status=status.HTTP_404_NOT_FOUND
            )

        user_away_service.set_user_away(away_reason)
        clear_user_cache(user)
        UserActivityLog.objects.create(
            request=request.data,
            response="",
            user_auth=user,
            user_id=user.code,
            activity_code=UserActivityLog.ActivityCode.ADD_USER_AWAY_ACTIVITY,
        )

        return Response(
            make_context(False, "I am away has been set successfully", None)
        )


class UserAwayDeleteApiView(APIView):
    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        user_away_id = request.data["user_away_id"]

        if not user:
            return Response(
                make_context(
                    True,
                    "No user found or you are not allowed to delete this tile",
                    status.HTTP_401_UNAUTHORIZED,
                )
            )

        user_away_delete_service = UserAwayDeleteService(user)
        success, message = user_away_delete_service.delete(user_away_id)

        if not success:
            return Response(make_context(True, message, status.HTTP_404_NOT_FOUND))
        clear_user_cache(user)
        UserActivityLog.objects.create(
            request=request.data,
            response=message,
            user_auth=user,
            user_id=user.code,
            activity_code=UserActivityLog.ActivityCode.DELETE_USER_AWAY_ACTIVITY,
        )
        return Response(make_context(False, message, status.HTTP_200_OK))


class UserAwayDeleteAllApiView(APIView):
    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        user_away_id = request.data["user_away_id"]

        if not user:
            return Response(
                make_context(
                    True,
                    "No user found or you are not allowed to delete this tile",
                    status.HTTP_401_UNAUTHORIZED,
                )
            )

        user_away_delete_service = UserAwayDeleteService(user)
        success, message = user_away_delete_service.delete_all(user_away_id)

        if not success:
            return Response(make_context(True, message, status.HTTP_404_NOT_FOUND))
        clear_user_cache(user)
        UserActivityLog.objects.create(
            request=request.data,
            response=message,
            user_auth=user,
            user_id=user.code,
            activity_code=UserActivityLog.ActivityCode.DELETE_USER_AWAY_ACTIVITY,
        )
        return Response(make_context(False, message, status.HTTP_200_OK))


class SessionPairingView(APIView):
    """Pairs a session with the current days planned session and returns the new session metadata"""

    activity_code = UserActivityLog.ActivityCode.SESSION_PAIRING

    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        actual_id = request.data.get("actual_id", False)

        if not actual_id:
            logger.error(f"No actual session id is provided. User id: {user.id}")
            response = make_context(True, "No session id is provided", None)
            return PillarResponse(
                user, request, response, self.activity_code, status.HTTP_404_NOT_FOUND
            )

        session_metadata = (
            SessionPairingService.pair_completed_session_with_planned_session(
                actual_id, user
            )
        )
        if session_metadata:
            clear_user_cache(user)
            response = make_context(
                False, "Session paired successfully", session_metadata
            )
            status_code = status.HTTP_200_OK
        else:
            response = make_context(True, "Could not pair session", None)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return PillarResponse(user, request, response, self.activity_code, status_code)


class SessionUnpairingView(APIView):
    """Unpairs a session from the currently paired planned session and returns the new session metadata"""

    activity_code = UserActivityLog.ActivityCode.SESSION_UNPAIRING

    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        actual_id = request.data.get("actual_id", False)

        if not actual_id:
            logger.error(f"No actual session id is provided. User id: {user.id}")
            response = make_context(True, "No session id is provided", None)
            return PillarResponse(
                user, request, response, self.activity_code, status.HTTP_404_NOT_FOUND
            )

        session_metadata = (
            SessionPairingService.unpair_evaluated_session_from_planned_session(
                actual_id, user
            )
        )
        if session_metadata:
            clear_user_cache(user)
            response = make_context(
                False, "Session unpaired successfully", session_metadata
            )
            status_code = status.HTTP_200_OK
        else:
            response = make_context(True, "Could not unpair session", None)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return PillarResponse(user, request, response, self.activity_code, status_code)


class CancelPairingMessageView(APIView):
    """Updates the show_pairing_message field of the actual session after the user has canceled the pairing message"""

    activity_code = UserActivityLog.ActivityCode.CANCEL_SESSION_PAIRING_MESSAGE

    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        actual_id = request.data.get("actual_id", False)

        if not actual_id:
            logger.error(f"No actual session id is provided. User id: {user.id}")
            response = make_context(True, "No session id is provided", None)
            return PillarResponse(
                user, request, response, self.activity_code, status.HTTP_404_NOT_FOUND
            )

        try:
            actual_session = get_actual_session(user, actual_id)
            actual_session.show_pairing_message = False
            actual_session.save()

            clear_user_cache(user)
            response = make_context(
                False,
                "Session pairing message cancellation recorded successfully",
                None,
            )
            status_code = status.HTTP_200_OK

        except ActualSession.DoesNotExist:
            logger.exception(
                f"Session pairing message record error, session with provided id does not exist. "
                f"Actual session id: {actual_id}, User id: {user.id}"
            )
            response = make_context(
                True, "Session with provided id does not exist", None
            )
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return PillarResponse(user, request, response, self.activity_code, status_code)


class SessionDeleteView(APIView):
    """
    Deletes the completed session of provided actual session id and recalculates
    previous days to reflect the changes.
    """

    activity_code = UserActivityLog.ActivityCode.SESSION_DELETE

    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        actual_id = request.data.get("actual_id", False)

        if not actual_id:
            logger.error(f"No actual session id is provided. User id: {user.id}")
            response = make_context(True, "No session id is provided", None)
            return PillarResponse(
                user, request, response, self.activity_code, status.HTTP_404_NOT_FOUND
            )

        try:
            current_session = get_actual_session(user, actual_id)
            SessionService.delete_session(current_session, user)
            notifications = Notification.objects.filter(
                data=current_session.code, is_active=True
            )
            if not notifications:
                current_session_date = current_session.session_date_time.date()
                current_session_utc_date = current_session.utc_session_date_time.date()
                notifications = Notification.objects.filter(
                    data__in=(current_session_date, current_session_utc_date),
                    recipient_id=user.id,
                    is_active=True,
                )  # For running activities
            update_is_active_value(notifications, False)

            clear_user_cache(user)
            response = make_context(False, "Session deleted successfully", None)
            status_code = status.HTTP_200_OK

        except Exception as e:
            logger.exception(
                f"Delete session failed for User id: {user.id}. Exception: {str(e)}."
            )
            response = make_context(True, "Could not delete session", None)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return PillarResponse(user, request, response, self.activity_code, status_code)


class SessionEditView(APIView):
    """Edits the session with provided actual session id according to the given information"""

    activity_code = UserActivityLog.ActivityCode.SESSION_EDIT

    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        actual_id = request.data.get("session_metadata", False)["actual_id"]
        planned_id = request.data.get("session_metadata", False)["planned_id"]
        session_status = request.data.get("session_metadata", False)["session_status"]
        is_manual_activity = request.data.get("session_metadata", False)[
            "is_manual_activity"
        ]
        activity_name = request.data.get("activity_name", False)
        activity_label = request.data.get("activity_label", False)
        description = request.data.get("activity_description", False)
        effort_level = request.data.get("effort_level", False)

        if not actual_id:
            logger.error(f"No actual session id is provided. User id: {user.id}")
            response = make_context(True, "No session id is provided", None)
            return PillarResponse(
                user, request, response, self.activity_code, status.HTTP_404_NOT_FOUND
            )

        try:
            if (
                is_manual_activity
                and session_status.lower() != SessionStatusEnum.PAIRED.value.lower()
            ):
                actual_session = get_actual_session(user, actual_id)
                update_achievement_data(user, actual_session)
                actual_session.is_active = False
                actual_session.save(update_fields=["is_active"])
                input_obj = ManualActivityService.get_manual_activity_input(
                    request, user
                )
                _, _, session_metadata = ManualActivityService.record_manual_activity(
                    user, input_obj, planned_id
                )
            else:
                session_metadata = SessionService.edit_session(
                    actual_id,
                    user,
                    activity_name,
                    activity_label,
                    description,
                    effort_level,
                    planned_id,
                )
            clear_user_cache(user)
            response = make_context(
                False, "Session edited successfully", session_metadata
            )
            status_code = status.HTTP_200_OK

        except Exception as e:
            logger.exception(
                f"Session edit failed for User id: {user.id}. Exception: {str(e)}."
            )
            response = make_context(True, "Could not edit session", None)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return PillarResponse(user, request, response, self.activity_code, status_code)


class SessionWarningView(APIView):
    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        try:
            actual_id = request.data.get("actual_id", False)
            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = user.email + ":" + "session_warning_view" + "-" + str(actual_id)

            if cache_key in cache and not force_refresh:
                warnings = cache.get(cache_key)
            else:
                warnings = SessionDetailServiceV2.get_warning_messages(user, actual_id)
                cache.set(cache_key, warnings, timeout=settings.CACHE_TIME_OUT)

            response = make_context(
                False, "Warnings retrieved successfully", data={"warnings": warnings}
            )
        except Exception as e:
            msg = "Failed to retrieve session warning"
            logger.exception(
                msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    user_auth_id=user.id,
                    request_url=request.path,
                    service_type=ServiceType.API.value,
                ),
            )
            response = make_context(True, msg, data={"warnings": []})

        return Response(response)


class SessionWarningDismissView(APIView):
    """Deactivates a session warning notification and message after it has been dismissed by the user"""

    activity_code = UserActivityLog.ActivityCode.SESSION_WARNING_DISMISS
    warning_notification_type_codes = [
        NotificationTypeEnum.HIGH_SINGLE_RIDE_LOAD.value[0],
        NotificationTypeEnum.HIGH_RECENT_TRAINING_LOAD.value[0],
        NotificationTypeEnum.CONSECUTIVE_HIGH_INTENSITY_SESSIONS.value[0],
    ]

    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        actual_id = request.data.get("actual_id", False)

        if not actual_id:
            logger.error(f"No actual session id is provided. User id: {user.id}")
            response = make_context(True, "No session id is provided", None)
            return PillarResponse(
                user, request, response, self.activity_code, status.HTTP_404_NOT_FOUND
            )

        try:
            code = get_actual_session(user, actual_id).code
            notifications = Notification.objects.filter(
                data=code,
                is_active=True,
                notification_type_id__in=self.warning_notification_type_codes,
            )
            update_is_active_value(notifications, False)

            cache_key = user.email + ":" + "session_warning_view" + "-" + str(actual_id)
            clear_cache_with_key(cache_key)
            response = make_context(
                False, "Session warning dismissed successfully", None
            )
            status_code = status.HTTP_200_OK

        except Exception as e:
            logger.exception(
                f"Failed to dismiss session warning for User id: {user.id}. Exception: {str(e)}."
            )
            response = make_context(True, "Failed to dismiss session warning", None)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return PillarResponse(user, request, response, self.activity_code, status_code)
