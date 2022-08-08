import datetime
import logging

from core.apps.session.models import ActualSession
from core.apps.session.tasks import is_cron_already_done_for_user
from core.apps.settings.models import UserSettings, UserSettingsQueue
from core.apps.settings.user_settings_type_codes import SettingsCode
from core.apps.settings.utils import update_settings_queue
from core.apps.user_profile.models import UserActivityLog

logger = logging.getLogger(__name__)


def update_utp_settings(user_id, status, priority, active_from, reason):

    settings_kwargs = {
        "user_id": user_id,
        "name": "auto update",
        "code": SettingsCode.AUTO_UPDATE_SETTINGS_CODE,
        "setting_status": status,
        "type": UserSettingsQueue.SettingsType.SYSTEM,
        "active_from": active_from,
        "task_priority": priority,
        "task_status": UserSettingsQueue.QueueTaskStatus.PENDING,
        "updated_by": "application",
        "reason": reason,
    }
    update_settings_queue(settings_kwargs)


def training_file_processed_within_last_seven_days(user):
    today = datetime.datetime.now()
    day_before_seven_days = today - datetime.timedelta(days=7)
    user_actual_sessions = ActualSession.objects.filter(
        user_auth=user,
        is_active=True,
        session_date_time__gte=day_before_seven_days,
        session_date_time__lte=today,
    )
    for actual_session in user_actual_sessions:
        if not actual_session.is_recovery_session():
            return True
    return False


def get_data_details_dict(user, reason):
    data_details_dict = {"user_id": user.id, "reason": reason}

    return data_details_dict


def is_user_valid_for_auto_update(user, start_time, first_cron_start_time, cron_code):
    if not user.user_plans.filter(
        is_active=True, end_date__gt=start_time.date()
    ).exists():
        return False

    if is_cron_already_done_for_user(
        user, start_time, first_cron_start_time, cron_code
    ):
        logger.info(f"Update cron already executed for user {user.email}")
        return False

    user_auto_update_setting = UserSettings.objects.filter(
        user_auth=user, code=SettingsCode.AUTO_UPDATE_SETTINGS_CODE
    ).last()
    if not user_auto_update_setting:
        logger.error("No auto update settings found")
        return False

    file_processed = training_file_processed_within_last_seven_days(user)
    if not user_auto_update_setting.status or not file_processed:
        if not user_auto_update_setting.status:
            data_details = get_data_details_dict(user, user_auto_update_setting.reason)
        else:
            data_details = get_data_details_dict(
                user, "no training file uploaded in last seven days"
            )
        user_activity_log = UserActivityLog(
            user_auth=user,
            user_id=user.code,
            data=data_details,
            activity_code=UserActivityLog.ActivityCode.AUTO_UPDATE_FAILED_FOR_USER,
        )
        user_activity_log.save()
        return False
    return True
