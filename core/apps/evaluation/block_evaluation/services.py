import logging

from .utils import get_total_blocks, get_user_blocks

logger = logging.getLogger(__name__)


class UserBlockEvaluation:

    # Depreciated from R7
    @classmethod
    def get_training_block_details(cls, user):
        user_plan = user.user_plans.filter(is_active=True).last()
        onboarding_date = user_plan.start_date

        try:
            user_event = user_plan.user_event
        except Exception as e:
            logger.exception(str(e) + "User Event Not found")
            return None
        event_date_time = user_event.event_date

        user_blocks = get_total_blocks(onboarding_date, event_date_time, user)
        return user_blocks

    @classmethod
    def training_block_details(cls, user):
        user_plan = user.user_plans.filter(is_active=True).last()
        onboarding_date = user_plan.start_date

        try:
            user_event = user_plan.user_event
        except Exception as e:
            logger.exception(str(e) + "User Event Not found")
            return None
        event_date_time = user_event.event_date

        user_blocks = get_user_blocks(onboarding_date, event_date_time, user)
        return user_blocks
