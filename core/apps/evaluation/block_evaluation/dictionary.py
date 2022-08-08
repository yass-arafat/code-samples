from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.messages import RECOVERY_DAY_MESSAGE


def get_single_block_session_dictionary(
    zone_focus,
    month_no,
    is_completed,
    planned_pss,
    building_week_no,
    recovery_week_no,
    block_sessions,
):
    single_block_dict = {
        "zone_focus": zone_focus,
        "month_no": month_no,
        "is_completed": is_completed,
        "planned_pss": planned_pss,
        "building_week_no": building_week_no,
        "recovery_week_no": recovery_week_no,
        "block_sessions": block_sessions,
    }
    return single_block_dict


# Depreciated from R7
def make_block_session_dict(planned_session, actual_session, timezone_offset):
    block_session_dict = {
        "id": planned_session.id,
        "date": DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, planned_session.session_date_time
        ),
        "session_type_name": planned_session.session_type_name,
        "session_timespan": round(
            planned_session.get_actual_duration(actual_session) * 3600
        )
        if actual_session
        else planned_session.planned_duration * 60,
        "is_evaluation_done": planned_session.is_evaluation_done,
        "session_name": planned_session.name,
        "zone_focus": planned_session.zone_focus,
        "is_completed": True if actual_session else False,
        "overall_accuracy_score": actual_session.session_score.get_overall_accuracy_score()
        if actual_session
        else None,
        "prs_accuracy_score": actual_session.session_score.get_prs_accuracy_score()
        if actual_session
        else None,
        # Depreciated from R8
        "overall_score": actual_session.session_score.get_overall_score()
        if actual_session
        else None,
        "prs_score": actual_session.session_score.get_prs_score()
        if actual_session
        else None,
        # Depreciated from R7
        "planned_duration": planned_session.planned_duration / 60,
        "actual_duration": planned_session.get_actual_duration(actual_session),
    }
    if planned_session.zone_focus == 0:
        block_session_dict["recovery_day_message"] = RECOVERY_DAY_MESSAGE

    return block_session_dict
