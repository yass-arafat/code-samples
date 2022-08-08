from django_rq import job

from core.apps.common.models import CronHistoryLog
from core.apps.user_auth.models import UserAuthModel

from .models import UserSettingsQueue
from .utils import update_user_settings


@job
def user_settings_queue_task():
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
                message = str(e)
                cron_status = CronHistoryLog.StatusCode.FAILED
            else:
                message = "updated user settings for user {0}".format(
                    user
                )  # update this line
                cron_status = CronHistoryLog.StatusCode.SUCCESSFUL
            CronHistoryLog.objects.create(
                cron_code=CronHistoryLog.CronCode.UPDATE_USER_SETTINGS,
                user_auth=user,
                user_id=user.code,
                status=cron_status,
            )
        else:
            message = "No pending user settings tasks for user {0}".format(
                user
            )  # update this line
        print(message)
