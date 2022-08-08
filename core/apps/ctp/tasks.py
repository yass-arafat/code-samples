import logging
from datetime import date, datetime, timedelta

from django_rq import job

from core.apps.common.common_functions import clear_user_cache
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import log_extra_fields
from core.apps.evaluation.daily_evaluation.utils import day_morning_calculation
from core.apps.plan.models import UserPlan
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.enums.user_access_level_enum import UserAccessLevelEnum
from core.apps.user_profile.models import UserProfile

from ..notification.services import update_today_focus_after_create_training_plan
from .services import CreateTrainingPlan

logger = logging.getLogger(__name__)


@job
def create_training_plan(user_id, plan_id, user_event):
    try:
        user_auth = UserAuthModel.objects.get(id=user_id, is_active=True)
        user_plan = UserPlan.objects.get(id=plan_id, is_active=True)
        CreateTrainingPlan(
            user_auth, user_plan, user_event, user_auth.training_availabilities.last()
        ).create_training_plan()

        user_profile = UserProfile.objects.filter(
            user_auth=user_auth, is_active=True
        ).last()
        user_profile.access_level = UserAccessLevelEnum.HOME.value[0]
        user_profile.save()

        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            user_auth.timezone_offset, datetime.now()
        )
        current_date = date.today()
        while current_date <= user_local_date:
            day_morning_calculation(user_auth, user_local_date)
            current_date += timedelta(days=1)
        update_today_focus_after_create_training_plan(user_auth)

        clear_user_cache(user_auth)
    except Exception as e:
        logger.exception(
            "Failed to create plan",
            extra=log_extra_fields(
                user_auth_id=user_id,
                service_type=ServiceType.API.value,
                exception_message=str(e),
            ),
        )
