import logging
from datetime import datetime, timedelta

from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.messages import KNOWLEDGE_HUB_NOTIFICATION_TITLE
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.services import PushNotificationService, create_notification
from core.apps.packages.models import KnowledgeHub, UserKnowledgeHub
from core.apps.plan.models import UserPlan

logger = logging.getLogger(__name__)


def create_user_knowledge_hub_entries(user, package_id):
    """Creates user knowledge hub entries right after creating a package plan"""
    logger.info(
        f"Start checking if knowledge hub entries will be created "
        f"for user id: {user.id}, package id: {package_id}"
    )
    knowledge_hub_entries = KnowledgeHub.objects.filter(
        package_id=package_id, is_active=True
    ).order_by("id")
    if not knowledge_hub_entries:
        logger.info(f"No knowledge hub found for package id: {package_id}")
        return

    logger.info("User knowledge hub entries will be created now")
    start_date = DateTimeUtils.get_user_local_date_from_utc(
        user.timezone_offset, datetime.now()
    )
    user_plan = UserPlan.objects.filter(
        user_auth=user,
        is_active=True,
        start_date__lte=start_date,
        end_date__gte=start_date,
    ).last()
    # When deleting a plan at the start date if planned session is already paired,
    # that planned session is not deleted and if user creates a plan again the same
    # day, it starts from the next day. Following query is for this specific case.
    if not user_plan:
        start_date += timedelta(days=1)
        user_plan = UserPlan.objects.filter(
            user_auth=user,
            is_active=True,
            start_date__lte=start_date,
            end_date__gte=start_date,
        ).last()

    user_knowledge_hub_entries = []

    for knowledge_hub_entry in knowledge_hub_entries:
        user_knowledge_hub_entry = UserKnowledgeHub(
            user_id=user.code,
            user_plan=user_plan,
            knowledge_hub=knowledge_hub_entry,
            activation_date=start_date,
        )
        user_knowledge_hub_entries.append(user_knowledge_hub_entry)
        start_date += timedelta(days=7)

    # Create first week notification for package knowledge hub
    UserKnowledgeHub.objects.bulk_create(user_knowledge_hub_entries)
    create_notification(
        user,
        NotificationTypeEnum.KNOWLEDGE_HUB,
        KNOWLEDGE_HUB_NOTIFICATION_TITLE,
        knowledge_hub_entries[0].notification_text,
        knowledge_hub_entries[0].id,
    )
    PushNotificationService(user).send_knowledge_hub_push_notification(
        knowledge_hub_entries[0].id, knowledge_hub_entries[0].title
    )
    logger.info("User knowledge hub entries are created successfully")
