import json
import logging
import uuid
from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max
from django.http import HttpRequest
from django.utils import timezone
from push_notifications.models import GCMDevice

from core.apps.common.common_functions import (
    clear_user_cache,
    get_timezone_offset_from_datetime_diff,
)
from core.apps.common.const import (
    HIGHEST_NOTIFICATION_SHOW,
    NOTIFICATIONS_PER_PAGE,
    TODAYS_NOTIFICATION_CRONJOB_TIME,
)
from core.apps.common.date_time_utils import (
    DateTimeUtils,
    add_time_to_datetime_obj,
    convert_str_date_to_date_obj,
)
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.date_time_format_enum import DateTimeFormatEnum
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.messages import (
    NEW_CYCLING_ACTIVITY_NOTIFICATION_BODY,
    NEW_CYCLING_ACTIVITY_NOTIFICATION_TITLE,
    NEW_RUNNING_ACTIVITY_NOTIFICATION_BODY,
    NEW_RUNNING_ACTIVITY_NOTIFICATION_TITLE,
    NOTIFICATION_PANEL_MESSAGE,
)
from core.apps.common.utils import (
    log_extra_fields,
    make_context,
    update_is_active_value,
)
from core.apps.session.models import ActualSession
from core.apps.settings.models import UserSettings
from core.apps.settings.user_settings_type_codes import SettingsCode
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.models import UserActivityLog, UserProfile

from ..common.models import CronHistoryLog
from .api.base.serializers import (
    InAppNotificationSerializer,
    NotificationHistorySerializer,
)
from .dictionary import (
    add_sync_init_dict,
    get_app_update_push_notification_dict,
    get_knowledge_hub_push_notification_dict,
    get_new_activity_push_notification_dict,
    get_notification_action_dict,
    get_notification_list_dict,
    get_notification_panel_dict,
    get_pagination_metadata_dict,
    get_payment_push_notification_dict,
    get_week_analysis_push_notification_dict,
)
from .enums.in_app_notification_enum import InAppNotificationActionType
from .enums.notification_type_enum import NotificationActionTypes, NotificationTypeEnum
from .enums.push_notification_enums import PushNotificationActionType
from .models import (
    InAppNotification,
    Notification,
    NotificationHistory,
    NotificationType,
    PushNotificationLog,
    PushNotificationSetting,
)

logger = logging.getLogger(__name__)


def get_notification_obj_from_request(request):
    notification = Notification()
    notification.title = request.data.get("title", "")
    notification.message = request.data.get("message", "")
    notification.recipient_type = request.data.get("recipient_type", -1)
    notification.recipient_id = request.data.get("recipient_id", None)
    notification.initiator_name = request.data.get("initiator_name", "")
    notification.initiator_id = request.data.get("initiator_id", None)

    type_id = request.data.get("notification_type", None)
    notification_type = NotificationType.objects.filter(pk=type_id).first()
    notification.notification_type = notification_type
    return notification


def get_notification_history_obj_from_request(request, notification, receiver):
    notification_history = NotificationHistory()
    notification_history.receiver = receiver
    notification_history.user_id = receiver.code
    notification_history.notification = notification
    notification_history.expired_at = add_time_to_datetime_obj(
        datetime.now(), receiver.notification_setting.last().expired_time
    )
    notification_history.action = request.data.get("action", -1)
    return notification_history


def get_notification_history_list_from_request(request, notification):
    notification_history_list = []

    recipient_type = request.data.get("recipient_type", -1)

    if recipient_type == Notification.RecipientType.INDIVIDUAL.value:
        receiver = UserAuthModel.objects.filter(pk=notification.recipient_id).first()
        notification_history = get_notification_history_obj_from_request(
            request, notification, receiver
        )
        notification_history_list.append(notification_history)
    elif recipient_type == Notification.RecipientType.ALL.value:
        users = UserAuthModel.objects.filter(is_active=True)
        for user in users:
            notification_history = get_notification_history_obj_from_request(
                request, notification, user
            )
            notification_history_list.append(notification_history)
    elif recipient_type == Notification.RecipientType.USER_GROUP.value:
        user_ids = request.data.get("user_ids", [])
        users = UserAuthModel.objects.filter(is_active=True, id__in=user_ids)
        for user in users:
            notification_history = get_notification_history_obj_from_request(
                request, notification, user
            )
            notification_history_list.append(notification_history)
    return notification_history_list


def get_user_notification(user):
    try:
        action = NotificationHistory.NotificationActionType.INITIATED.value
        user_notification_histories = NotificationHistory.objects.filter(
            receiver=user, notification__is_active=True, expired_at__gte=datetime.now()
        )
        notification_history = None
        notification_types = NotificationType.objects.filter(
            id__in=NotificationTypeEnum.today_focus_panel_ids()
        ).order_by("priority")
        for notification_type in notification_types:
            prioritized_notification_histories = user_notification_histories.filter(
                notification__notification_type=notification_type,
                notification__is_active=True,
            ).order_by("-created_at")
            notification_history = prioritized_notification_histories.first()
            if notification_history and notification_history.action == action:
                break

        user_profile = (
            user.profile_data.filter(is_active=True).select_related("timezone").first()
        )
        if notification_history:
            serialized = NotificationHistorySerializer(
                notification_history, context={"offset": user_profile.timezone.offset}
            )
            data = serialized.data
        else:
            data = {}
        data.update(get_notification_panel_dict(user_profile, user))
        error, msg, data = (
            False,
            "User Notification returned Successfully",
            None if not data else data,
        )
    except Exception as e:
        logger.exception(
            "Failed to save notification",
            extra=log_extra_fields(exception_message=str(e)),
        )
        error, msg, data = True, "Couldn't return user notification", None

    return error, msg, data


def update_user_notification(user, notification_id, request):
    try:
        action_type = request.data.get("actions", None)
        expired_at = add_time_to_datetime_obj(
            datetime.now(), user.notification_setting.last().expired_time
        )
        NotificationHistory.objects.create(
            receiver=user,
            user_id=user.code,
            notification_id=notification_id,
            action=action_type,
            expired_at=expired_at,
        )
        error, msg, data = False, "User Notification Updated Successfully", None
    except Exception as e:
        error, msg, data = True, "Update Notification failed", None
        logger.info(msg + str(e))
    UserActivityLog.objects.create(
        request=request.data,
        response=make_context(error, msg, data),
        user_auth=user,
        activity_code=UserActivityLog.ActivityCode.NOTIFICATION_CREATE,
        user_id=user.code,
    )
    return error, msg, data


def get_notification_history_obj(action, notification, receiver):
    notification_history = NotificationHistory()
    notification_history.receiver = receiver
    notification_history.user_id = receiver.code
    notification_history.notification = notification
    notification_history.expired_at = add_time_to_datetime_obj(
        datetime.now(), receiver.notification_setting.last().expired_time
    )
    notification_history.action = action
    return notification_history


def get_notification_dict(
    title,
    message,
    recipient_type,
    recipient_id,
    initiator_name,
    initiator_id,
    notification_type,
    data=None,
):
    notification_dict = {
        "title": title,
        "message": message,
        "recipient_type": recipient_type,
        "recipient_id": recipient_id,
        "initiator_name": initiator_name,
        "initiator_id": initiator_id,
        "notification_type": notification_type,
        "data": data,
    }
    return notification_dict


def get_today_probable_notifications_for_user(user):
    user_profile = user.profile_data.filter(is_active=True).last()
    probable_notifications_for_user = []
    initiator = User.objects.get(username=settings.CRON_USER_NAME)
    recipient_type = Notification.RecipientType.INDIVIDUAL
    user_local_date = DateTimeUtils.get_user_local_date_time_from_utc(
        user_profile.timezone.offset, datetime.now()
    ).strftime(DateTimeFormatEnum.app_date_format.value)
    today_session = user.planned_sessions.filter(
        session_date_time__date=user_local_date, is_active=True
    ).first()
    if not user.is_third_party_connected():
        notification_title = "No third party connected"
        notification_type_id = NotificationTypeEnum.NO_THIRD_PARTY_CONNECTED.value[0]
        notification_type = NotificationType.objects.get(id=notification_type_id)
        notification_message = "Hi {0} to get personalised evaluations connect your platforms in Settings.".format(
            user_profile.name
        )
        notification_dict = get_notification_dict(
            notification_title,
            notification_message,
            recipient_type,
            user.id,
            user_profile.name,
            initiator.id,
            notification_type,
        )
        no_third_party_connected_notification = Notification(**notification_dict)
        probable_notifications_for_user.append(no_third_party_connected_notification)

    if today_session:
        if today_session.session_type.code == "REST":
            notification_title = "Recovery day"
            notification_type_id = NotificationTypeEnum.RECOVERY_DAY.value[0]
            notification_type = NotificationType.objects.get(id=notification_type_id)
            notification_message = "Hi {0} the focus is a full Recovery Day. Take it easy and keep hydrated!".format(
                user_profile.name
            )
            notification_dict = get_notification_dict(
                notification_title,
                notification_message,
                recipient_type,
                user.id,
                user_profile.name,
                initiator.id,
                notification_type,
            )
            session_notification = Notification(**notification_dict)
        else:
            notification_title = "Today session"
            notification_type_id = NotificationTypeEnum.TODAY_SESSION.value[0]
            notification_type = NotificationType.objects.get(id=notification_type_id)
            notification_message = (
                "Hi {0}, the focus today is your session: {1}".format(
                    user_profile.name, today_session.name
                )
            )
            notification_dict = get_notification_dict(
                notification_title,
                notification_message,
                recipient_type,
                user.id,
                user_profile.name,
                initiator.id,
                notification_type,
            )
            session_notification = Notification(**notification_dict)
        probable_notifications_for_user.append(session_notification)

    return probable_notifications_for_user


def third_party_connect_notification(user):
    action = NotificationHistory.NotificationActionType.INITIATED.value
    notification_type_id = NotificationTypeEnum.NO_THIRD_PARTY_CONNECTED.value[0]
    notification_type = NotificationType.objects.get(id=notification_type_id)
    notification_history = (
        NotificationHistory.objects.filter(
            receiver=user, notification__notification_type=notification_type
        )
        .order_by("-created_at")
        .first()
    )
    if notification_history and notification_history.action == action:
        notification = notification_history.notification
        closed_action = NotificationHistory.NotificationActionType.CLOSED.value
        expired_at = add_time_to_datetime_obj(
            datetime.now(), user.notification_setting.last().expired_time
        )
        NotificationHistory.objects.create(
            receiver=user,
            user_id=user.code,
            notification=notification,
            action=closed_action,
            expired_at=expired_at,
        )


def third_party_disconnect_notification(user):
    user_profile = user.profile_data.filter(is_active=True).first()
    if not user.is_third_party_connected() and user_profile:
        notification_type_id = NotificationTypeEnum.NO_THIRD_PARTY_CONNECTED.value[0]
        notification_title = NotificationTypeEnum.NO_THIRD_PARTY_CONNECTED.value[1]
        notification_message = "Hi {0} to get personalised evaluations connect your platforms in Settings.".format(
            user_profile.name
        )
        recipient_type = Notification.RecipientType.INDIVIDUAL
        notification_type = NotificationType.objects.get(id=notification_type_id)
        notification_dict = get_notification_dict(
            notification_title,
            notification_message,
            recipient_type,
            user.id,
            user_profile.name,
            user.id,
            notification_type,
        )
        notification = Notification(**notification_dict)
        notification.save()
        initiate_action = NotificationHistory.NotificationActionType.INITIATED.value
        expired_at = add_time_to_datetime_obj(
            datetime.now(), user.notification_setting.last().expired_time
        )
        NotificationHistory.objects.create(
            receiver=user,
            user_id=user.code,
            notification=notification,
            action=initiate_action,
            expired_at=expired_at,
        )


def sync_user_actions(user_auth):
    user_last_sync = PushNotificationLog.objects.filter(
        notification_type=PushNotificationLog.NotificationType.SYNC, user_auth=user_auth
    ).last()

    user_actions = []
    if user_last_sync:
        user_push_notifications = PushNotificationLog.objects.filter(
            notification_type=PushNotificationLog.NotificationType.PUSH_NOTIFICATION,
            notification_status=PushNotificationLog.NotificationStatus.INITIATED,
            created_at__gt=user_last_sync.created_at,
            user_auth=user_auth,
        )
    else:
        user_push_notifications = PushNotificationLog.objects.filter(
            notification_type=PushNotificationLog.NotificationType.PUSH_NOTIFICATION,
            notification_status=PushNotificationLog.NotificationStatus.INITIATED,
            user_auth=user_auth,
        )

    for user_push_notification in user_push_notifications:
        copy_user_actions = user_push_notification.user_actions.copy()
        if user_push_notification.user_actions and copy_user_actions.get("sync_init"):
            user_actions.append(copy_user_actions.get("sync_init"))

    PushNotificationLog.objects.create(
        user_auth=user_auth,
        user_id=user_auth.code,
        notification_type=PushNotificationLog.NotificationType.SYNC,
    )

    return user_actions


def create_notification(
    user_auth,
    notification_type_enum,
    notification_title,
    notification_message,
    data=None,
    payment=None,
):
    """
    Creates entry in notification and notification history table and initiates a notification with given parameters.
    Parameter 'data' is optional and needed when some specific information related to the notification is needed to be
    saved e.g. actual session code for overtraining notification.
    """
    try:
        user_name = (
            user_auth.profile_data.filter(is_active=True)
            .values("name")
            .last()
            .get("name")
        )
        notification_type_id = notification_type_enum.value[0]
        recipient_type = Notification.RecipientType.INDIVIDUAL
        notification_type = NotificationType.objects.get(id=notification_type_id)
        notification_dict = get_notification_dict(
            notification_title,
            notification_message,
            recipient_type,
            user_auth.id,
            user_name,
            user_auth.id,
            notification_type,
            data,
        )
        logger.info("Saving notification")
        notification = Notification(**notification_dict)
        notification.save()
        initiate_action = NotificationHistory.NotificationActionType.INITIATED.value
        expired_at = add_time_to_datetime_obj(
            datetime.now(), user_auth.notification_setting.last().expired_time
        )
        logger.info("Creating notification history")
        NotificationHistory.objects.create(
            receiver=user_auth,
            user_id=user_auth.code,
            notification=notification,
            action=initiate_action,
            expired_at=expired_at,
        )
        logger.info("Clearing user cache")
        clear_user_cache(user_auth)

        logger.info(f"Payment = {payment}")
        if payment:  # hardcode not good, need refactor
            action_type = NotificationTypeEnum.get_push_notification_action_type(
                notification_type_enum.value[0]
            )
            PushNotificationService(user_auth).send_payment_push_notification(
                action_type=action_type
            )
        elif notification_type_enum.value[
            0
        ] in NotificationTypeEnum.push_notification_types() and isinstance(
            notification.data, uuid.UUID
        ):
            action_type = NotificationTypeEnum.get_push_notification_action_type(
                notification_type_enum.value[0]
            )
            logger.info(
                f"Sending push notification action_type = {action_type} user_auth = {user_auth.id}"
            )
            PushNotificationService(user_auth).send_new_activity_push_notification(
                action_type, notification
            )
    except Exception as e:
        logger.exception(
            "Failed to create notification",
            extra=log_extra_fields(
                user_auth_id=user_auth.id,
                service_type=ServiceType.INTERNAL.value,
                exception_message=str(e),
            ),
        )
        raise


def get_user_notification_list(user, last_id):
    """
    Filters the notifications of the user and return them.
    :param user: Current user whose notification is being returned.
    :param last_id: id of the last notification loaded on user's app. We need to return list of
    notifications for the next page after last_id.
    """
    showed_action = NotificationHistory.NotificationActionType.SHOWED.value
    initiated_action = NotificationHistory.NotificationActionType.INITIATED.value

    updated_notification_ids = get_action_type_updated_notification_ids(user)
    # Filter the notification histories which corresponds to the notifications which have only INITIATED action
    notification_histories = (
        NotificationHistory.objects.filter(
            receiver=user,
            action=initiated_action,
            notification__notification_type__in=NotificationTypeEnum.notification_panel_ids(),
        )
        .exclude(notification_id__in=updated_notification_ids)
        .values("notification")
    )
    update_notification_history_list = []
    for notification_history in notification_histories:
        notification_id = notification_history["notification"]
        update_notification_history_list.append(
            NotificationHistory(
                receiver=user,
                user_id=user.code,
                notification_id=notification_id,
                action=showed_action,
            )
        )
    NotificationHistory.objects.bulk_create(update_notification_history_list)

    notification_types = NotificationType.objects.filter(
        id__in=NotificationTypeEnum.notification_panel_ids()
    )
    all_notifications = Notification.objects.filter(
        notification_type__in=notification_types, recipient_id=user.id, is_active=True
    ).order_by("-created_at")
    start_index = (
        list(all_notifications.values("id")).index({"id": last_id}) + 1
        if last_id
        else 0
    )
    current_page_notifications = all_notifications[
        start_index : start_index + NOTIFICATIONS_PER_PAGE
    ]

    try:
        if all_notifications[start_index + NOTIFICATIONS_PER_PAGE + 1]:
            is_last = False
    except IndexError:
        is_last = True

    pagination_metadata = get_pagination_metadata_dict(
        all_notifications[start_index + NOTIFICATIONS_PER_PAGE - 1].id
        if not is_last
        else None,
        is_last,
    )
    notifications_list = []
    for notification in current_page_notifications:
        data = notification.data
        # Need to create a function for getting action type when there will be more notification types
        # and action types
        notification_action = get_notification_action_dict(notification, 0, data)
        notification_history = NotificationHistory.objects.filter(
            notification=notification
        ).last()
        is_read = notification_history.is_read()
        notification_dict = get_notification_list_dict(
            notification, notification_action, is_read
        )
        notifications_list.append(notification_dict)

    return {
        "pagination_metadata": pagination_metadata,
        "notifications": notifications_list,
    }


def get_activity_notification_attributes(
    activity_type, session_date, actual_session_code
):
    """Return respective notification title and body for activity_type"""
    notification_title = None
    notification_body = None
    data = None
    if activity_type == ActivityTypeEnum.CYCLING.value[1]:
        notification_title = NEW_CYCLING_ACTIVITY_NOTIFICATION_TITLE
        notification_body = NEW_CYCLING_ACTIVITY_NOTIFICATION_BODY
        data = actual_session_code
    elif activity_type == ActivityTypeEnum.RUNNING.value[1]:
        notification_title = NEW_RUNNING_ACTIVITY_NOTIFICATION_TITLE
        notification_body = NEW_RUNNING_ACTIVITY_NOTIFICATION_BODY
        data = session_date

    return notification_title, notification_body, data


def get_action_type_updated_notification_ids(user):
    """Returns the notification ids of the notifications of which action has been changed from INITIATED"""
    notification_ids = (
        NotificationHistory.objects.filter(
            receiver=user,
            notification__notification_type__in=NotificationTypeEnum.notification_panel_ids(),
        )
        .exclude(action=NotificationHistory.NotificationActionType.INITIATED.value)
        .values("notification")
        .distinct()
    )

    return notification_ids


def delete_last_today_focus_notification(user):
    try:
        last_today_focus_notification = Notification.objects.filter(
            recipient_id=user.id,
            notification_type__in=(
                NotificationTypeEnum.RECOVERY_DAY.value[0],
                NotificationTypeEnum.TODAY_SESSION.value[0],
            ),
            is_active=True,
        ).last()
        if last_today_focus_notification:
            last_today_focus_notification.is_active = False
            last_today_focus_notification.save()

    except Exception as e:
        logger.exception(
            "Could not deactivate last today focus after deleting plan",
            extra=log_extra_fields(
                user_auth_id=user.id,
                exception_message=str(e),
                service_type=ServiceType.INTERNAL.value,
            ),
        )


def update_today_focus_after_create_training_plan(user):
    """Updates the today focus notification of the user after creating a plan"""

    try:
        notification_objects = get_today_probable_notifications_for_user(user)
        notifications = Notification.objects.bulk_create(notification_objects)
        notification_history_list = []
        notification_history_action = (
            NotificationHistory.NotificationActionType.INITIATED.value
        )
        for notification in notifications:
            notification_history = get_notification_history_obj(
                notification_history_action, notification, user
            )
            notification_history_list.append(notification_history)
        NotificationHistory.objects.bulk_create(notification_history_list)

    except Exception as e:
        logger.exception(
            "Could not update today focus after running ctp",
            extra=log_extra_fields(
                user_auth_id=user.id,
                exception_message=str(e),
                service_type=ServiceType.INTERNAL.value,
            ),
        )


def send_auto_update_setting_notification(user, reason):
    if reason == "garmin connect":
        request_message = (
            "Connected platform detected, automatic update plan is enabled. "
            "Your plan will be personalised based on your progress at the end of each week."
        )
    elif reason == "garmin disconnect":
        request_message = (
            "No connected platforms, automatic update plan has been disabled. "
            "Please connect a third party data source to receive a more personalised plan."
        )
    elif reason == "48 hour rule":
        if user.garmin_user_token or user.strava_user_token:
            request_message = (
                "It's been two days since you joined Pillar, automatic update plan is enabled. "
                "Your plan will be personalised based on your progress at the end of each week."
            )
        else:
            return
    else:
        return

    initiator = User.objects.get(username=settings.CRON_USER_NAME)

    request = HttpRequest()
    request.data = {
        "title": "Auto Update Settings",
        "message": request_message,
        "recipient_type": Notification.RecipientType.INDIVIDUAL,
        "recipient_id": user.id,
        "initiator_name": user.profile_data.filter(is_active=True).first().name,
        "initiator_id": initiator.id,
        "notification_type": NotificationTypeEnum.AUTO_UPDATE_PLAN.value[0],
        "action": 1,
    }
    notification = get_notification_obj_from_request(request)

    notification.save()

    notification_history_list = get_notification_history_list_from_request(
        request, notification
    )
    NotificationHistory.objects.bulk_create(notification_history_list)

    response = make_context(False, "Notification created successfully.", None)
    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        activity_code=UserActivityLog.ActivityCode.NOTIFICATION_CREATE,
    )
    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        activity_code=UserActivityLog.ActivityCode.NOTIFICATION_UPDATE,
    )


def create_auto_update_notifications(user_ids):
    try:
        initiator = User.objects.get(username=settings.CRON_USER_NAME)
    except User.DoesNotExist:
        logger.error("Cron user not found")
        return
    request = HttpRequest()
    request.data = {
        "title": "Auto Update Plan",
        "message": "Updated training plan",
        "recipient_type": Notification.RecipientType.USER_GROUP,
        "recipient_id": None,
        "initiator_name": initiator.username,
        "initiator_id": initiator.id,
        "notification_type": NotificationTypeEnum.AUTO_UPDATE_PLAN.value[0],
        "action": 1,
        "user_ids": user_ids,
    }
    notification = get_notification_obj_from_request(request)

    notification.save()

    notification_history_list = get_notification_history_list_from_request(
        request, notification
    )
    NotificationHistory.objects.bulk_create(notification_history_list)

    response = make_context(False, "Notification created successfully.", None)
    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        activity_code=UserActivityLog.ActivityCode.NOTIFICATION_CREATE,
    )
    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        activity_code=UserActivityLog.ActivityCode.NOTIFICATION_UPDATE,
    )


def update_move_session_notification(user, source_day, target_session):
    user_profile = user.profile_data.filter(is_active=True).first()
    user_local_today = DateTimeUtils.get_user_local_date_time_from_utc(
        user.timezone_offset, datetime.now()
    )

    recipient_type = Notification.RecipientType.INDIVIDUAL
    if user_local_today.date() == source_day.activity_date:
        notification_title = "Recovery day"
        notification_type_id = NotificationTypeEnum.RECOVERY_DAY.value[0]
        notification_type = NotificationType.objects.get(id=notification_type_id)
        notification_message = "Hi {0} the focus is a full Recovery Day. Take it easy and keep hydrated!".format(
            user_profile.name
        )
    else:
        notification_title = "Today session"
        notification_type_id = NotificationTypeEnum.TODAY_SESSION.value[0]
        notification_type = NotificationType.objects.get(id=notification_type_id)
        notification_message = "Hi {0}, the focus today is your session: {1}".format(
            user_profile.name, target_session.name
        )
    notification_dict = get_notification_dict(
        notification_title,
        notification_message,
        recipient_type,
        user.id,
        user_profile.name,
        user.id,
        notification_type,
    )
    session_notification = Notification(**notification_dict)
    session_notification.save()
    notification_types = [
        NotificationTypeEnum.TODAY_SESSION.value[0],
        NotificationTypeEnum.RECOVERY_DAY.value[0],
    ]
    notification_history = NotificationHistory.objects.filter(
        receiver=user,
        expired_at__gte=datetime.now(),
        notification__is_active=True,
        notification__notification_type__in=notification_types,
    ).last()
    if notification_history:
        notification_history.notification.is_active = False
        notification_history.notification.save()
        notification_history.notification = session_notification
        notification_history.pk = None
        notification_history.save()


class NotificationService:
    def __init__(self, user_id, user_auth=None):
        self.user_id = user_id
        self.user_auth = user_auth
        if not self.user_auth:
            self.user_auth = UserAuthModel.objects.filter(code=user_id).last()

        self.extra_log_fields = log_extra_fields(
            user_auth_id=self.user_auth.id,
            user_id=self.user_id,
            service_type=ServiceType.INTERNAL.value,
        )

    def create_notification(self, request):
        notification_reason = request.data.get("notification_reason")
        if notification_reason == "new_activity":
            activity_type = request.data.get("activity_type")
            activity_date = request.data.get("activity_date")
            actual_session_code = request.data.get("actual_session_code")
            title, message, data = get_activity_notification_attributes(
                activity_type, activity_date, actual_session_code
            )
            return self.create_new_activity(title, message, data)
        elif notification_reason == "week_analysis":
            week_analysis_code = request.data.get("week_analysis_code")
            return self.create_week_analysis_notification(week_analysis_code)
        elif notification_reason == "move_session":
            activity_date = request.data.get("activity_date")
            activity_date = convert_str_date_to_date_obj(activity_date)

            session_name = request.data.get("session_name")
            return self.update_move_session_notification(activity_date, session_name)
        elif notification_reason == "delete_session":
            activity_dates = request.data.get("activity_dates")
            actual_session_code = request.data.get("actual_session_code")
            return self.delete_new_activity_notification(
                actual_session_code, activity_dates
            )
        elif notification_reason == "warning_dismiss":
            actual_session_code = request.data.get("actual_session_code")
            return self.delete_session_warning_notification(actual_session_code)
        elif notification_reason == "delete_today_focus":
            return self.delete_last_today_focus_notification()

    def create_new_activity(self, title, message, data, payment=None):
        try:
            user_name = (
                self.user_auth.profile_data.filter(is_active=True)
                .values("name")
                .last()
                .get("name")
            )
            notification_type_id = NotificationTypeEnum.NEW_ACTIVITY.value[0]
            recipient_type = Notification.RecipientType.INDIVIDUAL
            notification_type = NotificationType.objects.get(id=notification_type_id)
            notification_dict = get_notification_dict(
                title,
                message,
                recipient_type,
                self.user_auth.id,
                user_name,
                self.user_auth.id,
                notification_type,
                data,
            )
            logger.info("Saving notification")
            notification = Notification(**notification_dict)
            notification.save()
            initiate_action = NotificationHistory.NotificationActionType.INITIATED.value
            expired_at = add_time_to_datetime_obj(
                datetime.now(), self.user_auth.notification_setting.last().expired_time
            )
            logger.info("Creating notification history")
            NotificationHistory.objects.create(
                receiver=self.user_auth,
                user_id=self.user_id,
                notification=notification,
                action=initiate_action,
                expired_at=expired_at,
            )
            logger.info("Clearing user cache")
            clear_user_cache(self.user_auth)

            logger.info(f"Payment = {payment}")
            if payment:  # hardcode not good, need refactor
                action_type = NotificationTypeEnum.get_push_notification_action_type(
                    NotificationTypeEnum.NEW_ACTIVITY.value[0]
                )
                PushNotificationService(self.user_auth).send_payment_push_notification(
                    action_type=action_type
                )
            elif NotificationTypeEnum.NEW_ACTIVITY.value[
                0
            ] in NotificationTypeEnum.push_notification_types() and isinstance(
                notification.data, uuid.UUID
            ):
                action_type = NotificationTypeEnum.get_push_notification_action_type(
                    NotificationTypeEnum.NEW_ACTIVITY.value[0]
                )
                logger.info(
                    f"Sending push notification action_type = {action_type} user_auth = {self.user_auth.id}"
                )
                PushNotificationService(
                    self.user_auth
                ).send_new_activity_push_notification(action_type, notification)
        except Exception as e:
            logger.exception(
                "Failed to create notification",
                extra=log_extra_fields(
                    user_auth_id=self.user_auth.id,
                    service_type=ServiceType.INTERNAL.value,
                    exception_message=str(e),
                ),
            )
            raise

    def create_week_analysis_notification(self, week_analysis_code):
        logger.info("Creating week analysis notification", extra=self.extra_log_fields)

        push_notification_action_type = PushNotificationActionType.WEEK_ANALYSIS.value
        title, body = PushNotificationActionType.get_message(
            push_notification_action_type
        )

        recipient_type = Notification.RecipientType.INDIVIDUAL
        initiator = User.objects.get(username=settings.CRON_USER_NAME)

        notification_type_id = NotificationTypeEnum.WEEK_ANALYSIS.value[0]
        notification_type = NotificationType.objects.get(id=notification_type_id)

        notification_data = json.dumps({"week_analysis_id": str(week_analysis_code)})

        notification_dict = get_notification_dict(
            title,
            body,
            recipient_type,
            self.user_auth.id,
            initiator.username,
            initiator.id,
            notification_type,
            data=notification_data,
        )
        notification = Notification.objects.create(**notification_dict)
        self._create_notification_history(notification)
        return self._return_data(notification)

    def update_move_session_notification(self, activity_date, session_name):
        user_profile = self.user_auth.profile_data.filter(is_active=True).first()
        user_local_date = self.user_auth.user_local_date

        recipient_type = Notification.RecipientType.INDIVIDUAL
        if user_local_date == activity_date:
            notification_title = "Recovery day"
            notification_type_id = NotificationTypeEnum.RECOVERY_DAY.value[0]
            notification_type = NotificationType.objects.get(id=notification_type_id)
            notification_message = "Hi {0} the focus is a full Recovery Day. Take it easy and keep hydrated!".format(
                user_profile.name
            )
        else:
            notification_title = "Today session"
            notification_type_id = NotificationTypeEnum.TODAY_SESSION.value[0]
            notification_type = NotificationType.objects.get(id=notification_type_id)
            notification_message = (
                "Hi {0}, the focus today is your session: {1}".format(
                    user_profile.name, session_name
                )
            )
        notification_dict = get_notification_dict(
            notification_title,
            notification_message,
            recipient_type,
            self.user_auth.id,
            user_profile.name,
            self.user_auth.id,
            notification_type,
        )
        session_notification = Notification(**notification_dict)
        session_notification.save()
        notification_types = [
            NotificationTypeEnum.TODAY_SESSION.value[0],
            NotificationTypeEnum.RECOVERY_DAY.value[0],
        ]
        notification_history = NotificationHistory.objects.filter(
            receiver=self.user_auth,
            expired_at__gte=datetime.now(),
            notification__is_active=True,
            notification__notification_type__in=notification_types,
        ).last()
        if notification_history:
            notification_history.notification.is_active = False
            notification_history.notification.save()
            notification_history.notification = session_notification
            notification_history.pk = None
            notification_history.save()

    def delete_new_activity_notification(self, actual_session_code, activity_dates):
        notifications = Notification.objects.filter(
            data=actual_session_code, is_active=True
        )
        if not notifications:
            # For running activities
            notifications = Notification.objects.filter(
                data__in=activity_dates,
                recipient_id=self.user_auth.id,
                is_active=True,
            )
        notifications.update(is_active=False, updated_at=datetime.now())

    def delete_session_warning_notification(self, actual_session_code):
        warning_notification_type_codes = [
            NotificationTypeEnum.HIGH_SINGLE_RIDE_LOAD.value[0],
            NotificationTypeEnum.HIGH_RECENT_TRAINING_LOAD.value[0],
            NotificationTypeEnum.CONSECUTIVE_HIGH_INTENSITY_SESSIONS.value[0],
        ]

        Notification.objects.filter(
            data=actual_session_code,
            is_active=True,
            notification_type_id__in=warning_notification_type_codes,
        ).update(is_active=False, updated_at=datetime.now())

    def delete_last_today_focus_notification(self):
        try:
            last_today_focus_notification = Notification.objects.filter(
                recipient_id=self.user_auth.id,
                notification_type__in=(
                    NotificationTypeEnum.RECOVERY_DAY.value[0],
                    NotificationTypeEnum.TODAY_SESSION.value[0],
                ),
                is_active=True,
            ).last()
            if last_today_focus_notification:
                last_today_focus_notification.is_active = False
                last_today_focus_notification.save()

        except Exception as e:
            logger.exception(
                "Could not deactivate last today focus after deleting plan",
                extra=log_extra_fields(
                    user_id=self.user_id,
                    exception_message=str(e),
                    service_type=ServiceType.INTERNAL.value,
                ),
            )

    def _create_notification_history(self, notification):
        logger.info(
            "Creating week analysis notification history", extra=self.extra_log_fields
        )
        initiate_action = NotificationHistory.NotificationActionType.INITIATED.value
        expired_at = add_time_to_datetime_obj(
            datetime.now(), self.user_auth.notification_setting.last().expired_time
        )
        NotificationHistory.objects.create(
            receiver=self.user_auth,
            user_id=self.user_auth.code,
            notification=notification,
            action=initiate_action,
            expired_at=expired_at,
        )

    @staticmethod
    def _return_data(notification):
        return {"notification_id": notification.id}


class PushNotificationService:
    def __init__(self, user_auth):
        self.user_auth = user_auth

    def _extra_log_fields(self, exception_message=""):
        return log_extra_fields(
            exception_message=exception_message,
            user_auth_id=self.user_auth.id,
            user_id=self.user_auth.code,
            service_type=ServiceType.INTERNAL.value,
        )

    def send_push_notification_from_other_service(self, request):
        """Send push notification generated by other microservices"""

        if not self._is_push_notification_settings_enabled():
            return

        title = request.data["title"]
        body = request.data["body"]
        user_actions = request.data["user_actions"]

        self._send_message(title, body, user_actions)
        self._create_push_notification_log(user_actions)

    def send_knowledge_hub_push_notification(
        self, knowledge_hub_id, knowledge_hub_title
    ):
        try:
            if not self._is_push_notification_settings_enabled():
                return

            action_type = PushNotificationActionType.KNOWLEDGE_HUB.value
            title, body = PushNotificationActionType.get_message(action_type)
            body = body.format(knowledge_hub_title=knowledge_hub_title)
            user_actions = get_knowledge_hub_push_notification_dict(
                title, body, knowledge_hub_id
            )

            self._send_message(title, body, user_actions)
            self._create_push_notification_log(user_actions)

        except Exception as e:
            logger.exception(
                msg="Failed to send knowledge hub push notification.",
                extra=self._extra_log_fields(str(e)),
            )

    def send_week_analysis_push_notification(self, week_analysis):
        try:
            if not self._is_push_notification_settings_enabled():
                return

            action_type = PushNotificationActionType.WEEK_ANALYSIS.value
            title, body = PushNotificationActionType.get_message(action_type)
            user_actions = get_week_analysis_push_notification_dict(
                title, body, week_analysis
            )

            self._send_message(title, body, user_actions)
            self._create_push_notification_log(user_actions)

        except Exception as e:
            logger.exception(
                msg="Failed to send week analysis push notification.",
                extra=log_extra_fields(
                    exception_message=str(e),
                    user_auth_id=self.user_auth.id,
                    user_id=self.user_auth.code,
                    service_type=ServiceType.INTERNAL.value,
                ),
            )

    def send_payment_push_notification(self, action_type):
        try:
            if not self._is_push_notification_settings_enabled():
                return

            title, body = PushNotificationActionType.get_message(action_type)
            # 4 is needed for FE as mentioned in the link
            # https://www.notion.so/pillarapp/Notification-API-3412e6d0370544cf91bd523b1ddf0235#9294627d075a44eb9a0d8df04b817390
            user_actions = get_payment_push_notification_dict(
                title=title,
                body=body,
                action_name=action_type,
                # this action type is actually action_name here
                action_type_for_FE=4,
            )
            self._send_message(title, body, user_actions)

            param = {"title": title, "body": body}

            user_actions.update(add_sync_init_dict(name=action_type, param=param))

            self._create_push_notification_log(user_actions)

        except Exception as e:
            logger.exception(
                msg="Failed to send Payment push notification.",
                extra=self._extra_log_fields(str(e)),
            )

    def send_new_activity_push_notification(self, action_type, notification):
        try:
            from core.apps.session.utils import get_session_metadata

            if not self._is_push_notification_settings_enabled():
                return

            actual_session = ActualSession.objects.filter(code=notification.data).last()
            metadata = get_session_metadata(actual_session)
            title, body = PushNotificationActionType.get_message(action_type)
            action_type = NotificationActionTypes.ROUTE.value[0]
            user_actions = get_new_activity_push_notification_dict(
                title, body, action_type, notification.id, metadata
            )
            self._send_message(title, body, user_actions)
            self._create_push_notification_log(user_actions)

        except Exception as e:
            logger.exception(
                msg="Failed to send push notification.",
                extra=self._extra_log_fields(str(e)),
            )

    def send_app_update_push_notification(self, request_data):
        if not self._is_push_notification_settings_enabled():
            return

        action_type = PushNotificationActionType.APP_UPDATE.value
        title, body = PushNotificationActionType.get_message(action_type)
        android_link = request_data.get("android_link")
        ios_link = request_data.get("ios_link")
        notification_action_type = NotificationActionTypes.UPDATE.value[0]
        user_actions = get_app_update_push_notification_dict(
            title, body, notification_action_type, android_link, ios_link
        )

        self._send_message(title, body, user_actions)
        self._create_push_notification_log(user_actions)

    def _is_push_notification_settings_enabled(self):
        try:
            return UserSettings.objects.get(
                user_id=self.user_auth.code,
                code=SettingsCode.PUSH_NOTIFICATION_SETTINGS_CODE,
                is_active=True,
            ).status
        except UserSettings.DoesNotExist:
            logger.error(
                "User should have one active push notification setting",
                extra=self._extra_log_fields(),
            )
        except UserSettings.MultipleObjectsReturned:
            logger.error(
                "User should not have multiple active push notification settings",
                extra=self._extra_log_fields(),
            )

    def _send_message(self, title, body, user_actions):
        fcm_devices = GCMDevice.objects.filter(user=self.user_auth)
        try:
            fcm_devices.send_message(title=title, message=body, extra=user_actions)
        except Exception as e:
            logger.info(
                "Push notification falied", extra=self._extra_log_fields(str(e))
            )

    def _create_push_notification_log(self, user_actions):
        PushNotificationLog.objects.create(
            notification_type=PushNotificationLog.NotificationType.PUSH_NOTIFICATION,
            user_auth=self.user_auth,
            user_id=self.user_auth.code,
            user_actions=user_actions,
        )


class PushNotificationSettingService:
    def __init__(self, **kwargs):
        self.user_auth = kwargs["user_auth"]
        self.user_id = kwargs["user_id"]

    def update_push_notification_setting(self, token_type, old_token, new_token):
        if not self._is_push_notification_update_valid(old_token, new_token):
            return

        try:
            push_notification_settings = PushNotificationSetting.objects.filter(
                device_token=new_token
            )
            update_is_active_value(push_notification_settings, False)

            GCMDevice.objects.filter(
                registration_id=new_token, cloud_message_type="FCM"
            ).delete()

            user_push_notification_setting = PushNotificationSetting.objects.get(
                user_id=self.user_id,
                device_token=old_token,
                token_type=token_type,
                is_active=True,
            )
            user_push_notification_setting.device_token = new_token
            user_push_notification_setting.save()
            devices = GCMDevice.objects.filter(
                registration_id=old_token, user=self.user_auth
            )
            with transaction.atomic():
                for device in devices:
                    device.registration_id = new_token
                    device.save()

        except PushNotificationSetting.DoesNotExist:
            PushNotificationSetting.objects.create(
                user_id=self.user_id,
                device_token=new_token,
                token_type=token_type,
            )
            GCMDevice.objects.create(
                registration_id=new_token, cloud_message_type="FCM", user=self.user_auth
            )

    def delete_push_notification_setting(self, device_token: str):
        """Deactivate expired/invalid device_token"""
        if not device_token:
            return

        push_notification_settings = PushNotificationSetting.objects.filter(
            user_id=self.user_id, device_token=device_token, is_active=True
        )
        update_is_active_value(push_notification_settings, is_active=False)

        GCMDevice.objects.filter(
            registration_id=device_token, user=self.user_auth
        ).delete()

    def _is_push_notification_update_valid(self, old_token, new_token):
        if old_token == new_token or not new_token:
            return False

        token_already_exists = GCMDevice.objects.filter(
            registration_id=new_token, user=self.user_auth
        ).exists()
        if token_already_exists:
            return False

        return True


class TodayFocusMessageCronService:
    def __init__(self):
        self.start_time = datetime.now().replace(second=0, microsecond=0)
        self.timezone_offset = self._get_timezone_offset()
        logger.info(f"Staring Today Focus cron for timezone: {self.timezone_offset}")

        self.users = self._get_users()

    def _get_timezone_offset(self):
        return get_timezone_offset_from_datetime_diff(
            datetime.combine(date.today(), TODAYS_NOTIFICATION_CRONJOB_TIME)
            - self.start_time
        )

    def _get_users(self):
        user_id_queryset = (
            UserProfile.objects.filter(
                user_auth_id__isnull=False,
                is_active=True,
                timezone__offset=self.timezone_offset,
            )
            .values_list("user_auth_id")
            .annotate(Max("id"))
        )
        user_ids = []
        for i, obj in enumerate(user_id_queryset):
            user_ids.append(obj[0])
        return UserAuthModel.objects.filter(id__in=user_ids)

    def create_today_focus_notifications(self):
        try:
            notifications = self._get_notifications()
            notifications = Notification.objects.bulk_create(notifications)

            notification_history_list = self._get_notification_history_list(
                notifications
            )
            NotificationHistory.objects.bulk_create(notification_history_list)
        except Exception as e:
            logger.exception(
                f"Today notification update failed for timezone {self.timezone_offset}",
                extra=log_extra_fields(
                    exception_message=str(e), service_type=ServiceType.CRON.value
                ),
            )
        else:
            self._create_cron_logs()

    def _get_notifications(self):
        notifications = []
        for user in self.users:
            notifications.extend(get_today_probable_notifications_for_user(user))
        return notifications

    def _get_notification_history_list(self, notifications):
        notification_history_list = []
        action = NotificationHistory.NotificationActionType.INITIATED.value
        for notification in notifications:
            user = self.users.get(id=notification.recipient_id)
            notification_history = get_notification_history_obj(
                action, notification, user
            )
            notification_history_list.append(notification_history)

        return notification_history_list

    def _create_cron_logs(self):
        cron_logs = self._get_cron_logs()
        CronHistoryLog.objects.bulk_create(cron_logs)

    def _get_cron_logs(self):
        return [self._get_cron_history_object(user) for user in self.users]

    @staticmethod
    def _get_cron_history_object(user):
        cron_code = CronHistoryLog.CronCode.UPDATE_TODAY_NOTIFICATION
        cron_status = CronHistoryLog.StatusCode.SUCCESSFUL
        CronHistoryLog(
            cron_code=cron_code,
            user_auth=user,
            user_id=user.code,
            status=cron_status,
        )


class InAppNotificationSevice:
    def __init__(self, request):
        self.user_id = request.session["user_id"]

        # Create in app notification for user
        self.title = request.data.get("title")
        self.body = request.data.get("body")
        self.generated_by = request.data.get("generated_by")
        self.data = request.data.get("data")
        self.type = request.data.get("type")

        # update in app notification action for user
        self.action = request.data.get("action")
        self.notification_id = request.data.get("notification_id")

        # get in app notification for user
        self.last_id = request.GET.get("last_id")

    def _get_in_app_notifications(self):
        if self.last_id:
            self.last_id = int(self.last_id)
            notifications = InAppNotification.objects.filter(
                receiver_id=self.user_id, id__lt=self.last_id, is_active=True
            ).order_by("-id")
        else:
            notifications = InAppNotification.objects.filter(
                receiver_id=self.user_id, is_active=True
            ).order_by("-id")

        logger.info(f"returing notifications for user {self.user_id}")
        return notifications

    def get_notification_list(self):
        notifications = self._get_in_app_notifications()

        # update notification action as showed
        notifications.filter(
            action=InAppNotificationActionType.INITIATED.value[0]
        ).update(action=InAppNotificationActionType.SHOWED.value[0])
        logger.info(f"updated notification action as showed for user {self.user_id}")

        # notification pagination logic
        number_of_notifications = len(notifications)
        if number_of_notifications > NOTIFICATIONS_PER_PAGE:
            notifications = notifications[:NOTIFICATIONS_PER_PAGE]
            last_id = list(notifications)[-1].id
            is_last = False
        else:
            last_id = None
            is_last = True

        pagination_metadata = {
            "last_id": last_id,
            "is_last": is_last,
        }

        notification_list = InAppNotificationSerializer(notifications, many=True).data

        logger.info(f"returing notification list for user {self.user_id}")
        return {
            "pagination_metadata": pagination_metadata,
            "notifications": notification_list,
        }

    def create_notification(self):
        notification = InAppNotification.objects.create(
            receiver_id=self.user_id,
            title=self.title,
            body=self.body,
            generated_by=self.generated_by,
            data=self.data,
            type=self.type,
        )

        logger.info(
            f"notification created for user {self.user_id} notification_id {notification.id}"
        )
        return {"notification_id": notification.id}

    def update_notification(self):
        InAppNotification.objects.filter(
            receiver_id=self.user_id, id=self.notification_id
        ).update(action=self.action, updated_at=datetime.now(tz=timezone.utc))
        logger.info(
            f"notification action updated for user {self.user_id} notification_id {self.notification_id}"
        )


class NotificationPanelService:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")

    def get_notification_panel_data(self):
        logger.info(f"Fetcting notification panel data for user {self.user_id}")
        new_notification_count = self._get_new_notification_count()
        notification_panel_title = self._get_notification_panel_title()
        return {
            "title": notification_panel_title,
            "message": NOTIFICATION_PANEL_MESSAGE,
            "new_notification_count": new_notification_count,
        }

    def _get_new_notification_count(self):
        new_notification_count = InAppNotification.objects.filter(
            receiver_id=self.user_id,
            is_active=True,
            action=InAppNotificationActionType.INITIATED.value[0],
        ).count()

        if new_notification_count:
            new_notification_count = (
                str(new_notification_count)
                if new_notification_count < NOTIFICATIONS_PER_PAGE
                else HIGHEST_NOTIFICATION_SHOW
            )
        else:
            new_notification_count = None

        return new_notification_count

    def _get_notification_panel_title(self):
        user_profile = UserProfile.objects.filter(user_id=self.user_id).last()
        logger.info(f"fetcting notification panel title for user {self.user_id}")
        return f"Hello, {user_profile.name}"


class DeactivateInAppNotificationService:
    def __init__(self, request):
        self.user_id = request.session["user_id"]
        self.data = request.data
        self.type = request.data.get("type")
        self.notification_id = self._get_notification_id()

    def _get_notification_id(self):
        if self.type == NotificationTypeEnum.NEW_ACTIVITY.value[0]:
            return self._get_notification_id_for_new_activity()
        elif self.type == NotificationTypeEnum.TRAINING_FILE_UPLOAD_CHECK.value[0]:
            return self._get_notification_id_for_training_file_upload_check()

    def _get_notification_id_for_new_activity(self):
        notification_id = (
            InAppNotification.objects.filter(
                receiver_id=self.user_id,
                is_active=True,
                data__actual_code=self.data.get("actual_code"),
            )
            .last()
            .id
        )
        logger.info(f"returning notification_id for new activity {notification_id}")
        return notification_id

    def _get_notification_id_for_training_file_upload_check(self):
        notfication_id = self.data.get("notification_id")
        logger.info(
            f"returning notification_id for training file upload check {notfication_id}"
        )
        return notfication_id

    def deactivate_notification(self):
        InAppNotification.objects.filter(
            receiver_id=self.user_id, id=self.notification_id
        ).update(is_active=False, updated_at=datetime.now(tz=timezone.utc))
        logger.info(
            f"notification deactivated for user {self.user_id} notification_id {self.notification_id}"
        )
