import logging

from core.apps.notification.services import TodayFocusMessageCronService

logger = logging.getLogger(__name__)


# @shared_task
def update_today_focus_message_panel():
    TodayFocusMessageCronService().create_today_focus_notifications()
