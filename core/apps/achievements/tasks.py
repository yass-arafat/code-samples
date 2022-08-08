from core.apps.common.enums.activity_type import ActivityTypeEnum


def update_user_achievements(user, actual_session, average_speed):
    from core.apps.achievements.utils import check_personal_records

    if actual_session.activity_type == ActivityTypeEnum.CYCLING.value[1]:
        check_personal_records(user, actual_session, average_speed)
