from time import gmtime, strftime


def get_sessions_overview_dict(upcoming_rides=None, past_rides=None):
    return {
        "upcoming_rides": upcoming_rides if upcoming_rides else [],
        "past_rides": past_rides if past_rides else [],
    }


def get_session_details_dict_other_data(
    evaluation_scores,
    actual_time_in_power_zones_dict,
    actual_time_in_hr_zones_dict,
    planned_time_in_power_zones,
    planned_time_in_hr_zones,
    ride_summary_dict,
    is_ftp_available,
    is_fthr_available,
    activity_info,
    is_ftp_input_needed,
    is_fthr_input_needed,
    session_date_time,
    planned_interval_data,
    actual_interval_data,
    zone_name,
    session_metadata,
    zone_focus,
    session_name,
    show_pairing_message,
    show_pairing_option,
    session_description,
    planned_duration,
    planned_intensity,
    effort_level,
    edit_manual_activity_data,
    accuracy_scores,
    key_zones,
    accuracy_score_overview=None,
    activity_label=None,
    key_zone_description=None,
    planned_session_name=None,
    power_zone_performance=None,
    heart_rate_zone_performance=None,
    pairing_option_message=None,
    show_feedback_popup=None,
    session_followed_as_planned=None,
    feedback_reason=None,
):
    """Returns session details which is shown in session evaluation V2 page"""

    # deleting calories burnt object from activity info to provide backward
    # compatibility to old releases from R12 to onwards
    # this activity_info_old key is deprecated from R13. you can remove it after 3 releases
    from copy import copy

    activity_info_v2 = None
    if activity_info:
        activity_info_v2 = copy(activity_info)
        activity_info.pop(8)

    session_details = {
        "session_metadata": session_metadata,
        "session_name": session_name,
        "planned_session_name": planned_session_name,
        "session_date_time": session_date_time,
        "zone_focus": zone_focus,
        "zone_name": zone_name,
        "session_description": session_description,
        "accuracy_score_overview": accuracy_score_overview,
        "effort_level": effort_level,
        "activity_label": activity_label,
        "planned_duration": planned_duration,
        "planned_intensity": planned_intensity,
        "session_details": activity_info,
        "session_details_v2": activity_info_v2,
        "show_pairing_message": show_pairing_message,
        "pairing_option_message": pairing_option_message,
        "show_pairing_option": show_pairing_option,
        "evaluation_score": evaluation_scores,
        "accuracy_scores": accuracy_scores,
        "key_zone_data": {
            "zones": key_zones,
            "description": key_zone_description,
            "power_zone_performance": power_zone_performance,
            "heart_rate_zone_performance": heart_rate_zone_performance,
        },
        "actual_time_in_power_zone": actual_time_in_power_zones_dict,
        "actual_time_in_hr_zone": actual_time_in_hr_zones_dict,
        "target_time_in_power_zone": planned_time_in_power_zones,
        "target_time_in_hr_zone": planned_time_in_hr_zones,
        "ride_summary": ride_summary_dict,
        "planned_interval_data": planned_interval_data,
        "actual_interval_data": actual_interval_data,
        "is_ftp_available": is_ftp_available,
        "is_fthr_available": is_fthr_available,
        "is_ftp_input_needed": is_ftp_input_needed,
        "is_fthr_input_needed": is_fthr_input_needed,
        "edit_manual_activity_data": edit_manual_activity_data,
        "show_feedback_popup": show_feedback_popup,
        "session_followed_as_planned": session_followed_as_planned,
        "feedback_reason": feedback_reason,
    }
    return session_details


def get_session_info_dict_v2(
    moving_time,
    elapsed_time,
    distance,
    average_speed,
    elevation,
    intensity,
    pss,
    weighted_power,
    calories_burnt,
):
    return [
        {
            "type": "Moving Time",
            "value": strftime("%H:%M:%S", gmtime(moving_time))
            if moving_time is not None
            else None,
        },
        {
            "type": "Elapsed Time",
            "value": strftime("%H:%M:%S", gmtime(elapsed_time))
            if elapsed_time is not None
            else None,
        },
        {
            "type": "Distance",
            "value": f"{distance} km" if distance is not None else None,
        },
        {
            "type": "Average Speed",
            "value": f"{average_speed} km/h" if average_speed is not None else None,
        },
        {
            "type": "Elevation",
            "value": f"{elevation} m" if elevation is not None else None,
        },
        {
            "type": "Intensity",
            "value": f"{intensity} %" if intensity is not None else None,
        },
        {
            "type": "PSS",
            "value": f"{pss} PSS" if pss is not None else None,
        },
        {
            "type": "Weighted Power",
            "value": f"{weighted_power} W" if weighted_power is not None else None,
        },
        {
            "type": "Calories Burnt",
            "value": f"{calories_burnt} kcal" if calories_burnt is not None else None,
        },
    ]
