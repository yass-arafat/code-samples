import logging
import uuid
from datetime import datetime, timedelta

from django.db import transaction

from core.apps.common.common_functions import clear_user_cache
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.ctp.tasks import create_training_plan
from core.apps.session.models import ActualSession

from .models import UserPlan
from .services import DeleteTrainingPlan

logger = logging.getLogger(__name__)


def create_plan(user_auth, user_event=None):
    if not user_event:
        user_event = user_auth.user_events.filter(is_active=True).last()

    plan_start_date = DateTimeUtils.get_user_local_date_from_utc(
        user_auth.timezone_offset, datetime.now()
    )
    if user_auth.user_plans.filter_active(end_date=plan_start_date).exists():
        plan_start_date += timedelta(days=1)

    logger.info("Creating plan...")
    plan = UserPlan.objects.create(
        user_auth=user_auth,
        user_id=user_auth.code,
        user_event=user_event,
        start_date=plan_start_date,
        end_date=user_event.end_date,
        plan_code=uuid.uuid4(),
    )
    create_training_plan(user_auth.id, plan.id, user_event)


@transaction.atomic
def delete_goal(user_auth):
    """Deletes the current plan of user"""
    user_local_date = DateTimeUtils.get_user_local_date_from_utc(
        user_auth.timezone_offset, datetime.now()
    )
    today_paired_session = ActualSession.objects.filter(
        user_auth=user_auth,
        is_active=True,
        session_code__isnull=False,
        session_date_time__date=user_local_date,
    )
    if today_paired_session:
        new_plan_end_date = user_local_date
    else:
        new_plan_end_date = user_local_date - timedelta(days=1)

    DeleteTrainingPlan(user_auth, new_plan_end_date).delete_user_plan()
    logger.info(f"Deleted goal for user: {user_auth.id}")
    clear_user_cache(user_auth)
