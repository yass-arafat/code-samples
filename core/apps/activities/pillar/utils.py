import logging
from datetime import timedelta

from django.db import transaction

from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.tp_common_utils import get_third_party_instance
from core.apps.common.utils import create_new_model_instance, get_ride_summary_v2
from core.apps.evaluation.daily_evaluation.utils import set_actual_day_data
from core.apps.evaluation.session_evaluation.utils import (
    calculate_session,
    check_overtraining,
)
from core.apps.session.utils import get_session_metadata
from core.apps.user_profile.utils import get_user_fthr, get_user_ftp

from ...achievements.tasks import update_user_achievements
from ...challenges.tasks import update_user_challenge
from ...common.services import RoundServices
from .models import Activity

logger = logging.getLogger(__name__)


def create_manual_activity_data_instance(
    duration, distance, average_power, average_speed, average_heart_rate, activity_type
):
    from .services import ActivityObject

    activity = ActivityObject()
    activity.distance = distance
    activity.moving_time = duration
    activity.average_power = average_power
    activity.average_heart_rate = average_heart_rate
    activity.average_speed = average_speed
    activity.activity_type = activity_type

    return activity


def create_activity_data_instance(
    user_auth,
    activity_name,
    activity_type,
    activity_label,
    duration,
    distance,
    average_power,
    average_heart_rate,
    stress_level,
):
    activity = Activity()
    activity.name = activity_name
    activity.type = activity_type
    activity.label = activity_label
    activity.total_distance_in_meter = distance
    activity.elapsed_time_in_seconds = duration
    activity.average_power = average_power
    activity.average_heart_rate = average_heart_rate
    activity.stress_level = stress_level
    activity.user_auth = user_auth
    activity.user_id = user_auth.code

    return activity


def calculate_manual_activity_data(
    user_auth,
    activity_obj,
    activity_date_time,
    utc_activity_date_time,
    activity_data_model,
    planned_id,
    effort_level,
    activity_description,
    activity_name,
    activity_label,
    actual_session=None,
):
    user_ftp = get_user_ftp(user_auth, activity_date_time)
    user_fthr = get_user_fthr(user_auth, activity_date_time)

    actual_session, planned_today, actual_yesterday = calculate_session(
        user_auth=user_auth,
        user_ftp=user_ftp,
        user_fthr=user_fthr,
        third_party_data=activity_obj,
        activity_datetime=activity_date_time,
        utc_activity_datetime=utc_activity_date_time,
        actual_session=actual_session,
    )
    logger.info("finished manual calculate_session")

    actual_session.third_party = get_third_party_instance(
        ThirdPartySources.MANUAL.value[0]
    )
    actual_session.pillar_data = activity_data_model
    actual_session.effort_level = effort_level
    actual_session.description = activity_description
    actual_session.activity_name = activity_name
    actual_session.session_label = activity_label
    actual_session.activity_type = activity_obj.activity_type
    actual_session.reason = "Manual activity process"
    actual_session.save()

    if (
        planned_today
        and activity_data_model.activity_type == ActivityTypeEnum.CYCLING.value[1]
    ):
        check_overtraining(actual_session, actual_yesterday, planned_today, user_auth)

    actual_today = set_actual_day_data(planned_today, actual_session)
    if actual_today:
        """
        If it's a completely new actual day, then there will be no created_at and updated_at
        and we should not make is_active=false and insert new row. we will just save a new actual day instance
        """
        if actual_today.created_at:
            actual_today = create_new_model_instance(actual_today)
            actual_today.reason = "Manual activity process"
        actual_today.save()

        update_user_achievements(user_auth, actual_session, activity_obj.average_speed)
        update_user_challenge(user_auth, actual_session)

        current_date = activity_date_time.date()
        user_local_date = user_auth.user_local_date
        if current_date != user_local_date:
            date_from = current_date + timedelta(days=1)
            user_plan = actual_session.user_plan
            if user_plan:
                with transaction.atomic():
                    from ..services import ReevaluationService

                    ReevaluationService.reevaluate_session_data_of_single_plan(
                        user_auth, user_plan, date_from
                    )

    session_metadata = get_session_metadata(
        actual_session=actual_session, planned_id=planned_id
    )

    logger.info("finish strava create_new_model_instance")
    return False, "Manual Activity Data Saved Successfully", session_metadata


def add_manual_data_to_model(
    activity_obj, user_auth, activity_type, activity_date_time
):
    activity_data = Activity()

    activity_data.activity_type = activity_type
    activity_data.user_auth = user_auth
    activity_data.user_id = user_auth.code
    activity_data.moving_time_in_seconds = activity_obj.moving_time
    activity_data.average_power = activity_obj.average_power
    activity_data.average_heart_rate = activity_obj.average_heart_rate
    activity_data.average_speed = activity_obj.average_speed
    activity_data.total_distance_in_meter = activity_obj.distance

    activity_data.save()
    return activity_data


def get_average_speed_from_ride_summary(ride_summary):
    """Retrieves average speed from"""
    average_speed = None
    ride_summary = get_ride_summary_v2(ride_summary)
    for summary in ride_summary:
        if summary["type"] == "Speed" and summary["average"]:
            average_speed = RoundServices.round_speed(float(summary["average"]))

    return average_speed


def get_max_cadence_from_ride_summary(ride_summary):
    """Retrieves average speed from"""
    cadence = None
    ride_summary = get_ride_summary_v2(ride_summary)
    for summary in ride_summary:
        if summary["type"] == "Cadence" and "max" in summary:
            cadence = RoundServices.round_speed(float(summary["max"]))

    return cadence
