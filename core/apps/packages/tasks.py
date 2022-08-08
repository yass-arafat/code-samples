import logging
from datetime import date, datetime, timedelta

import requests
from celery import shared_task
from django.conf import settings

from core.apps.common.common_functions import get_timezone_offset_from_datetime_diff
from core.apps.common.const import FIRST_TIMEZ0NE_OFFSET, KNOWLEDGE_HUB_TIP_CRONJOB_TIME
from core.apps.common.date_time_utils import time_diff_between_two_timezone_offsets
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.messages import KNOWLEDGE_HUB_NOTIFICATION_TITLE
from core.apps.common.models import CronHistoryLog
from core.apps.common.utils import log_extra_fields
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.services import (
    PushNotificationService,
    create_notification,
    update_today_focus_after_create_training_plan,
)
from core.apps.packages.enums import GoalTypeEnum
from core.apps.packages.models import Package, UserKnowledgeHub, UserPackage
from core.apps.packages.services import (
    CreateHillClimbPackagePlan,
    CreateReturnToCyclingPackagePlan,
)
from core.apps.session.tasks import is_cron_already_done_for_user
from core.apps.user_auth.models import UserAuthModel

logger = logging.getLogger(__name__)


@shared_task
def create_package_plan(user_id, package_id, package_duration):
    try:
        user_package = UserPackage.objects.filter(
            user_id=user_id, is_active=True
        ).last()
        package = Package.objects.get(id=package_id)

        if package.goal_type == GoalTypeEnum.LIFESTYLE.value[0]:
            CreateReturnToCyclingPackagePlan(
                user_package
            ).create_package_training_plan()

        if package.goal_type == GoalTypeEnum.PERFORMANCE.value[0]:
            package_duration *= 7  # weeks to days
            CreateHillClimbPackagePlan(
                user_package, package_duration
            ).create_package_training_plan()

        # Update today focus notification after plan creation
        user = UserAuthModel.objects.filter(code=user_id).last()
        update_today_focus_after_create_training_plan(user)

    except Exception as e:
        logger.exception(
            "Failed to create package plan",
            extra=log_extra_fields(
                user_auth_id=user_id,
                service_type=ServiceType.INTERNAL.value,
                exception_message=str(e),
            ),
        )


def send_knowledge_hub_tip_notification():
    """Cron task function for sending weekly knowledge hub notifications to the users"""
    try:
        start_time = datetime.now().replace(second=0, microsecond=0)

        timezone_offset = get_timezone_offset_from_datetime_diff(
            datetime.combine(date.today(), KNOWLEDGE_HUB_TIP_CRONJOB_TIME) - start_time
        )
        first_cron_time_diff = time_diff_between_two_timezone_offsets(
            FIRST_TIMEZ0NE_OFFSET, timezone_offset
        )
        first_cron_start_time = start_time - timedelta(seconds=first_cron_time_diff)

        cron_code = CronHistoryLog.CronCode.KNOWLEDGE_HUB_TIP
        cron_logs = []

        today_user_knowledge_hub_entries = UserKnowledgeHub.objects.filter(
            is_active=True, activation_date=start_time.date()
        )

        try:
            for user_knowledge_hub in today_user_knowledge_hub_entries:
                user = UserAuthModel.objects.filter(
                    code=user_knowledge_hub.user_id,
                    profile_data__timezone__offset=timezone_offset,
                    profile_data__is_active=True,
                    is_active=True,
                ).last()
                if not user:
                    logger.info(
                        f"No user is found with user code: {user_knowledge_hub.user_id}"
                    )
                    continue
                if is_cron_already_done_for_user(
                    user, start_time, first_cron_start_time, cron_code
                ):
                    continue

                try:
                    knowledge_hub = user_knowledge_hub.knowledge_hub
                    create_notification(
                        user,
                        NotificationTypeEnum.KNOWLEDGE_HUB,
                        KNOWLEDGE_HUB_NOTIFICATION_TITLE,
                        user_knowledge_hub.knowledge_hub.notification_text,
                        knowledge_hub.id,
                    )
                    PushNotificationService(user).send_knowledge_hub_push_notification(
                        knowledge_hub.id, knowledge_hub.title
                    )
                except Exception:
                    cron_status = CronHistoryLog.StatusCode.FAILED
                else:
                    cron_status = CronHistoryLog.StatusCode.SUCCESSFUL

                cron_logs.append(
                    CronHistoryLog(
                        cron_code=cron_code,
                        user_auth=user,
                        user_id=user.code,
                        status=cron_status,
                    )
                )

            CronHistoryLog.objects.bulk_create(cron_logs)

        except Exception as e:
            logger.error(
                f"Send knowledge hub tip notification cron failed for timezone "
                f"{timezone_offset}. Exception: {str(e)}"
            )

    except Exception as e:
        logger.exception(
            f"Send knowledge hub tip notification cron failed. Exception: {e}"
        )
        requests.post(
            url=settings.ASYNC_HEALTHCHECK_URL + "/fail",
            data={"Exception": e, "Cron": "Knowledge Hub Tip"},
        )
