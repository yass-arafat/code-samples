import logging

from django.core.management.base import BaseCommand

from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.models import CronHistoryLog
from core.apps.common.utils import log_extra_fields
from core.apps.user_auth.models import UserAuthModel

from ...models import UserSettingsQueue
from ...utils import update_user_settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update user settings"

    def handle(self, *args, **kwargs):
        users = UserAuthModel.objects.filter(is_active=True)
        pending_tasks_in_settings_queue = UserSettingsQueue.objects.filter(
            task_status=UserSettingsQueue.QueueTaskStatus.PENDING
        )

        for user in users:
            user_pending_tasks = pending_tasks_in_settings_queue.filter(user_auth=user)
            if user_pending_tasks:
                try:
                    update_user_settings(user_pending_tasks)
                except Exception as e:
                    cron_status = CronHistoryLog.StatusCode.FAILED
                    logger.exception(
                        "Failed to update user settings",
                        extra=log_extra_fields(
                            user_auth_id=user.id,
                            service_type=ServiceType.CRON.value,
                            exception_message=str(e),
                        ),
                    )
                else:
                    cron_status = CronHistoryLog.StatusCode.SUCCESSFUL
                    logger.info(
                        "Successfully updated user settings",
                        extra=log_extra_fields(
                            user_auth_id=user.id, service_type=ServiceType.CRON.value
                        ),
                    )

                CronHistoryLog.objects.create(
                    cron_code=CronHistoryLog.CronCode.UPDATE_USER_SETTINGS,
                    user_auth=user,
                    user_id=user.code,
                    status=cron_status,
                )
