from django_rq import job

from core.apps.common.utils import create_new_model_instance
from core.apps.session.models import ActualSession


@job
def recalculate_single_session(user_auth, actual_session_id):
    actual_session = ActualSession.objects.get(
        pk=actual_session_id, user_auth=user_auth
    )

    if actual_session.pillar_data_id:
        from core.apps.activities.pillar.utils import (
            calculate_manual_activity_data,
            create_manual_activity_data_instance,
        )

        manual_activity = actual_session.pillar_data
        activity_obj = create_manual_activity_data_instance(
            duration=manual_activity.moving_time_in_seconds,
            distance=manual_activity.total_distance_in_meter,
            average_power=manual_activity.average_power,
            average_speed=manual_activity.average_speed,
            average_heart_rate=manual_activity.average_heart_rate,
            activity_type=manual_activity.activity_type,
        )

        actual_session = create_new_model_instance(actual_session)
        calculate_manual_activity_data(
            user_auth=user_auth,
            activity_obj=activity_obj,
            activity_date_time=actual_session.session_date_time,
            utc_activity_date_time=actual_session.utc_session_date_time,
            activity_data_model=manual_activity,
            planned_id=None,
            effort_level=actual_session.effort_level,
            activity_description=actual_session.description,
            activity_name=actual_session.activity_name,
            activity_label=actual_session.session_label,
            actual_session=actual_session,
        )

    return actual_session
