from core.apps.challenges.services import ChallengeService
from core.apps.common.enums.activity_type import ActivityTypeEnum


def update_user_challenge(user, actual_session):
    if actual_session.activity_type == ActivityTypeEnum.CYCLING.value[1]:
        ChallengeService.update_user_challenge_data(user, actual_session)
