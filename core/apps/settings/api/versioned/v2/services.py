import datetime
import logging

from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.notification.models import UserNotificationSetting
from core.apps.settings.utils import create_initial_settings
from core.apps.utp.utils import update_utp_settings

logger = logging.getLogger(__name__)


class SettingsService:
    @staticmethod
    def save_user_initial_settings(user_id):
        UserNotificationSetting.objects.create(user_id=user_id)
        create_initial_settings(user_id)

        logger.info("Updating utp settings ....")
        update_utp_settings(
            user_id,
            False,
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[1],
            datetime.datetime.now(),
            reason="new user",
        )
