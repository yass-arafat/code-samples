import datetime
import logging

from core.apps.common.utils import create_new_model_instance

from ..notification.services import send_auto_update_setting_notification
from ..user_profile.models import UserProfile
from .models import UserSettings, UserSettingsQueue
from .user_settings_type_codes import SettingsCode

logger = logging.getLogger(__name__)


def update_user_settings(user_pending_tasks):
    unique_setting_type_codes = user_pending_tasks.values("code").distinct()
    for setting_type_code in unique_setting_type_codes:
        user_settings = user_pending_tasks.filter(
            code=setting_type_code["code"]
        ).order_by("task_priority", "active_from")
        for setting in user_settings:
            task_status = update_setting(setting)
            if task_status:
                setting.task_status = UserSettingsQueue.QueueTaskStatus.COMPLETED
                setting.save()
                send_auto_update_setting_notification(setting.user_auth, setting.reason)
            else:
                break


def update_setting(setting) -> bool:
    now = datetime.datetime.now()
    if setting.active_from.replace(tzinfo=None) <= now:
        user = setting.user_auth
        user_setting, created = UserSettings.objects.get_or_create(
            user_auth=user, user_id=user.code, code=setting.code, is_active=True
        )
        user_setting.name = setting.name
        user_setting.status = setting.setting_status
        user_setting.settings_type = setting.type
        user_setting.updated_by = setting.updated_by
        user_setting.reason = setting.reason
        user_setting.save()
        return True
    return False


def update_settings_queue(kwargs):
    UserSettingsQueue.objects.create(**kwargs)


def create_push_notification_settings(user_id):
    user_setting, _ = UserSettings.objects.get_or_create(
        user_id=user_id,
        code=SettingsCode.PUSH_NOTIFICATION_SETTINGS_CODE,
    )
    user_setting.name = "Push Notification Settings"
    user_setting.status = True
    user_setting.settings_type = UserSettings.SettingsType.USER
    user_setting.updated_by = "application"
    user_setting.reason = "new user"
    user_setting.save()


def update_push_notification_settings(user_setting, status, updated_by, reason):
    user_setting = create_new_model_instance(user_setting)
    user_setting.status = status
    user_setting.updated_by = updated_by
    user_setting.reason = reason
    user_setting.save()


def create_initial_settings(user_id):
    create_push_notification_settings(user_id)


def get_access_level(user_id):
    """Returns the current access level of the user"""

    logger.info(f"Fetching access level of user id {user_id}")

    user_profile = UserProfile.objects.filter(user_id=user_id, is_active=True).last()

    return user_profile.access_level if user_profile else "PROFILE"
