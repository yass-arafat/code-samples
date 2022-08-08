from core.apps.common.messages import RECOVERY_DAY_MESSAGE


def get_past_ride_dict(
    planned_session, session_timespan, date, session_planned_duration, actual_session
):
    past_ride_dict = {
        "id": planned_session.id,
        "date": date,
        "session_name": planned_session.name,
        "session_type_name": planned_session.session_type_name,
        "zone_focus": planned_session.zone_focus,
        "is_completed": planned_session.is_completed,
        "is_evaluation_done": planned_session.is_evaluation_done,
        "session_timespan": session_timespan,
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
        "planned_duration": session_planned_duration,
        "actual_duration": actual_session.actual_duration / 60
        if actual_session
        else None,
    }
    if planned_session.zone_focus == 0:
        past_ride_dict["recovery_day_message"] = RECOVERY_DAY_MESSAGE

    return past_ride_dict


def get_upcoming_ride_dict(
    planned_session, session_timespan, date, session_planned_duration
):
    upcoming_ride_dict = {
        "id": planned_session.id,
        "date": date,
        "session_name": planned_session.name,
        "session_type_name": planned_session.session_type_name,
        "zone_focus": planned_session.zone_focus,
        "planned_duration": session_planned_duration,  # Depreciated from R7
        "session_timespan": session_timespan,
        # For backwards compatibility, delete when no one is using R3 anymore
        "session_type": planned_session.session_type_name,
        "planned_session_duration": session_planned_duration,
    }
    if planned_session.zone_focus == 0:
        upcoming_ride_dict["recovery_day_message"] = RECOVERY_DAY_MESSAGE
    return upcoming_ride_dict


def get_today_dictionary(
    date_today,
    zone_focus_name,
    zone_focus,
    starting_prs,
    current_prs,
    target_prs,
    rides_completed,
    rides_total,
    total_plan_distance,
    days_due_of_event,
    upcoming_rides,
    past_rides,
):
    todays_data_dict = {
        "today_date": date_today,
        "zone_focus_name": zone_focus_name,
        "zone_focus": zone_focus,
        "starting_prs": starting_prs,
        "current_prs": current_prs,
        "target_prs": target_prs,
        "rides_completed": rides_completed,
        "rides_total": rides_total,
        "total_plan_distance": total_plan_distance,
        "days_due_of_event": days_due_of_event,
        "upcoming_rides": upcoming_rides,
        "past_rides": past_rides,
    }

    return todays_data_dict
