import logging

from django.db import transaction

from core.apps.common.common_functions import clear_user_cache
from core.apps.user_auth.models import UserAuthModel

from .services import EditTrainingPlan

logger = logging.getLogger(__name__)


@transaction.atomic
def edit_training_plan(user_id, new_event_date):
    user = UserAuthModel.objects.get(id=user_id)
    current_plan = user.user_plans.filter(is_active=True).last()
    previous_event_date = current_plan.user_event.start_date

    if previous_event_date < new_event_date:
        EditTrainingPlan(user.id, new_event_date).edit_goal_forward()
    elif previous_event_date > new_event_date:
        EditTrainingPlan(user.id, new_event_date).edit_goal_backward()
    clear_user_cache(user)
    return True, "Failed"
