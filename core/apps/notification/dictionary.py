import json

from core.apps.common.const import HIGHEST_NOTIFICATION_SHOW, NOTIFICATIONS_PER_PAGE
from core.apps.common.messages import (
    NEW_CYCLING_ACTIVITY_NOTIFICATION_TITLE,
    NEW_OTHER_ACTIVITY_NOTIFICATION_TITLE,
    NEW_ROWING_ACTIVITY_NOTIFICATION_TITLE,
    NEW_RUNNING_ACTIVITY_NOTIFICATION_TITLE,
    NEW_STRENGTH_ACTIVITY_NOTIFICATION_TITLE,
    NEW_SWIMMING_ACTIVITY_NOTIFICATION_TITLE,
    NEW_WALKING_ACTIVITY_NOTIFICATION_TITLE,
    NEW_WELLBEING_ACTIVITY_NOTIFICATION_TITLE,
    NOTIFICATION_PANEL_MESSAGE,
)
from core.apps.notification.const import FLUTTER_NOTIFICATION_CLICK
from core.apps.notification.enums.in_app_notification_enum import (
    InAppNotificationButtonType,
    InAppNotificationClickActionType,
)
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.models import Notification
from core.apps.notification.notification_icon_urls import NOTIFICATION_ICON_URLS
from core.apps.session.models import ActualSession


def get_pagination_metadata_dict(last_id, is_last):
    """
    Returns data needed for notification pagination.
    :param last_id: The id of the last notification of current page.
    :param is_last: True if this is the last page of notification list, otherwise returns false.
    """
    return {"last_id": last_id, "is_last": is_last}


def get_notification_action_dict(notification, action_type, data):
    # TODO: Implement a better way of getting action metadata for different type of notifications
    notification_type = notification.notification_type.id
    notification_title = notification.title
    name = None
    params = None
    url = None
    if notification_type in (
        NotificationTypeEnum.THIRD_PARTY_ACCOUNT_LINKED.value[0],
        NotificationTypeEnum.THIRD_PARTY_PROFILE_DISCONNECTED.value[0],
    ):
        name = "CONNECTED_PLATFORM"
    elif notification_type == NotificationTypeEnum.HISTORIC_ACTIVITY_SYNC.value[0]:
        name = "CALENDAR"
        params = data
    elif notification_type == NotificationTypeEnum.NEW_ACTIVITY.value[0]:
        from core.apps.session.utils import get_session_metadata

        if notification_title == NEW_CYCLING_ACTIVITY_NOTIFICATION_TITLE:
            name = "SESSION_DETAILS"
            actual_session = ActualSession.objects.filter(
                code=data, is_active=True
            ).last()
            params = get_session_metadata(actual_session)
        elif notification_title == NEW_RUNNING_ACTIVITY_NOTIFICATION_TITLE:
            name = "CALENDAR"
            params = {"date": data}
    elif notification_type == NotificationTypeEnum.WEEK_ANALYSIS.value[0]:
        name = "WEEK_ANALYSIS"
        params = json.loads(data)
    elif notification_type == NotificationTypeEnum.KNOWLEDGE_HUB.value[0]:
        name = "KNOWLEDGE_HUB"
        params = {"id": int(data)}  # id is stored as textfield, need to convert to int
    elif notification_type == NotificationTypeEnum.PAYMENT_INITIAL_SUCCESS.value[0]:
        name = "PAYMENT_INITIAL_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.PAYMENT_RENEWAL_SUCCESS.value[0]:
        name = "PAYMENT_RENEWAL_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.PAYMENT_CANCEL_SUCCESS.value[0]:
        name = "PAYMENT_CANCEL_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.PAYMENT_EXPIRE_SUCCESS.value[0]:
        name = "PAYMENT_EXPIRE_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.TRIAL_EXPIRE_SUCCESS.value[0]:
        name = "TRIAL_EXPIRE_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.KNOWLEDGE_HUB.value[0]:
        name = "KNOWLEDGE_HUB"
        params = {"id": int(data)}  # id is stored as textfield, need to convert to int

    return {
        "action_type": action_type,
        "action_metadata": {"name": name, "params": params, "url": url},
    }


def get_notification_list_dict(notification, notification_action, is_read):
    return {
        "id": notification.id,
        "title": notification.title,
        "body": notification.message,
        "time": notification.created_at,
        "icon": NOTIFICATION_ICON_URLS[notification.title],
        "is_read": is_read,
        "notification_action": notification_action,
    }


def get_notification_panel_dict(user_profile, user):
    from core.apps.notification.services import get_action_type_updated_notification_ids

    updated_notification_ids = get_action_type_updated_notification_ids(user)
    new_notification_count = (
        Notification.objects.filter(
            recipient_id=user.id,
            notification_type__in=NotificationTypeEnum.notification_panel_ids(),
        )
        .exclude(id__in=updated_notification_ids)
        .count()
    )
    if new_notification_count:
        new_notification_count = (
            str(new_notification_count)
            if new_notification_count < NOTIFICATIONS_PER_PAGE
            else HIGHEST_NOTIFICATION_SHOW
        )
    else:
        new_notification_count = None

    return {
        "notification_panel_title": f"Hello, {user_profile.name}",
        "notification_panel_message": NOTIFICATION_PANEL_MESSAGE,
        "new_notification_count": new_notification_count,
    }


def get_base_push_notification_dict(title, body, action_type=None):
    return {
        "title": title,
        "body": body,
        "action_type": action_type,
        "click_action": FLUTTER_NOTIFICATION_CLICK,
    }


def get_app_update_push_notification_dict(
    title, body, action_type, android_link, ios_link
):
    push_notification_dict = get_base_push_notification_dict(title, body, action_type)
    push_notification_dict.update({"android": android_link, "ios": ios_link})
    return push_notification_dict


def get_new_activity_push_notification_dict(
    title, body, action_type, notification_id, params
):
    push_notification_dict = get_base_push_notification_dict(title, body, action_type)
    push_notification_dict.update(
        {"action_name": "SESSION_DETAILS", "id": notification_id, "params": params}
    )
    return push_notification_dict


def get_payment_push_notification_dict(title, body, action_name, action_type_for_FE):
    push_notification_dict = get_base_push_notification_dict(
        title, body, action_type_for_FE
    )
    push_notification_dict.update({"action_name": action_name})
    return push_notification_dict


def add_sync_init_dict(name, param):
    return {
        "sync_init": {
            "name": name,
            "param": param,
        }
    }


def get_week_analysis_push_notification_dict(title, body, week_analysis):
    push_notification_dict = get_base_push_notification_dict(title, body, action_type=3)
    push_notification_dict.update(
        {
            "action_name": "WEEKLY_ANALYSIS",
            "week_analysis_id": str(week_analysis.code),
            "week_start_date": str(week_analysis.week_start_date),
            "week_end_date": str(week_analysis.week_end_date),
        }
    )
    return push_notification_dict


def get_knowledge_hub_push_notification_dict(title, body, knowledge_hub_id):
    push_notification_dict = get_base_push_notification_dict(title, body, action_type=0)
    push_notification_dict.update(
        {"action_name": "KNOWLEDGE_HUB", "id": knowledge_hub_id}
    )
    return push_notification_dict


# new in app notification action dict
def get_in_app_notification_action_dict(notification):
    notification_type = notification.type
    notification_title = notification.title
    data = notification.data
    name = None
    params = None
    url = None
    action_type = InAppNotificationClickActionType.ROUTE.value[0]
    if notification_type in (
        NotificationTypeEnum.THIRD_PARTY_ACCOUNT_LINKED.value[0],
        NotificationTypeEnum.THIRD_PARTY_PROFILE_DISCONNECTED.value[0],
    ):
        name = "CONNECTED_PLATFORM"
    elif notification_type == NotificationTypeEnum.HISTORIC_ACTIVITY_SYNC.value[0]:
        name = "CALENDAR"
        params = data
    elif notification_type == NotificationTypeEnum.NEW_ACTIVITY.value[0]:
        if notification_title in (
            NEW_CYCLING_ACTIVITY_NOTIFICATION_TITLE,
            NEW_RUNNING_ACTIVITY_NOTIFICATION_TITLE,
            NEW_WALKING_ACTIVITY_NOTIFICATION_TITLE,
            NEW_SWIMMING_ACTIVITY_NOTIFICATION_TITLE,
            NEW_STRENGTH_ACTIVITY_NOTIFICATION_TITLE,
            NEW_ROWING_ACTIVITY_NOTIFICATION_TITLE,
            NEW_WELLBEING_ACTIVITY_NOTIFICATION_TITLE,
            NEW_OTHER_ACTIVITY_NOTIFICATION_TITLE,
        ):
            name = "SESSION_DETAILS"
            params = data
    elif notification_type == NotificationTypeEnum.WEEK_ANALYSIS.value[0]:
        name = "WEEK_ANALYSIS"
        params = data
    elif notification_type == NotificationTypeEnum.KNOWLEDGE_HUB.value[0]:
        name = "KNOWLEDGE_HUB"
        params = data
    elif notification_type == NotificationTypeEnum.PAYMENT_INITIAL_SUCCESS.value[0]:
        name = "PAYMENT_INITIAL_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.PAYMENT_RENEWAL_SUCCESS.value[0]:
        name = "PAYMENT_RENEWAL_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.PAYMENT_CANCEL_SUCCESS.value[0]:
        name = "PAYMENT_CANCEL_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.PAYMENT_EXPIRE_SUCCESS.value[0]:
        name = "PAYMENT_EXPIRE_SUCCESS"
        params = ""
    elif notification_type == NotificationTypeEnum.TRIAL_EXPIRE_SUCCESS.value[0]:
        name = "TRIAL_EXPIRE_SUCCESS"
        params = ""

    return {
        "action_type": action_type,
        "action_metadata": {"name": name, "params": params, "url": url},
    }


def get_in_app_notification_button_action_dict(notification):
    notification_type = notification.type

    if notification_type == NotificationTypeEnum.TRAINING_FILE_UPLOAD_CHECK.value[0]:
        button_actions = get_training_file_upload_check_button_action(notification)
        return button_actions
    elif NotificationTypeEnum.is_week_analysis_notification(notification_type):
        button_actions = get_week_analysis_notification_button_action(
            notification, notification_type
        )
        return button_actions
    else:
        return None


def button_action_dict(
    button_title,
    button_type,
    action_type=None,
    name=None,
    params=None,
    url=None,
):
    return {
        "title": button_title,
        "type": button_type,
        "action": {
            "action_type": action_type,
            "action_metadata": {
                "name": name,
                "params": params,
                "url": url,
            },
        },
    }


def get_training_file_upload_check_button_action(notification):
    action_type = InAppNotificationClickActionType.API.value[0]
    name = "TRAINING_FILE_UPLOAD_CHECK"
    button_type = InAppNotificationButtonType.BAR.value[0]

    yes_button_title = "Yes, I have more files"
    yes_button_params = notification.data.get("yes_button_params")
    yes_button_params["notification_id"] = notification.id
    yes_button_action = button_action_dict(
        yes_button_title, button_type, action_type, name, yes_button_params
    )

    no_button_title = "No, I’ve uploaded all my files"
    no_button_params = notification.data.get("no_button_params")
    no_button_params["notification_id"] = notification.id
    no_button_action = button_action_dict(
        no_button_title, button_type, action_type, name, no_button_params
    )

    button_actions = [yes_button_action, no_button_action]
    return button_actions


def get_week_analysis_notification_button_action(notification, notification_type):
    if (
        notification_type
        == NotificationTypeEnum.PROVISIONAL_WEEK_ANALYSIS_REPORT_UPDATE.value[0]
    ):
        title = "View Updated Analysis"
    else:
        title = "View Analysis"
    action_type = InAppNotificationClickActionType.ROUTE.value[0]
    button_type = InAppNotificationButtonType.REGULAR.value[0]
    action_name = "WEEK_ANALYSIS"
    params = notification.data
    button_actions = button_action_dict(
        title, button_type, action_type, action_name, params
    )

    return [button_actions]
