import math

from core.apps.common.common_functions import CommonClass


def get_session_details_dict(
    actual_power_data,
    planned_power_data,
    actual_hr_data,
    planned_hr_data,
    evaluation_scores,
    actual_time_in_power_zones,
    actual_time_in_hr_zones,
    planned_time_in_power_zones,
    planned_time_in_hr_zones,
    ride_summary_dict,
    cur_ftp,
    cur_fthr,
    profile_variable,
):
    session_details = {
        "actual_power_graph_data": actual_power_data,
        "target_power_graph_data": planned_power_data,
        "actual_hr_graph_data": actual_hr_data,
        "target_hr_graph_data": planned_hr_data,
        "evaluation_score": evaluation_scores,
        "actual_time_in_power_zone": actual_time_in_power_zones,
        "actual_time_in_hr_zone": actual_time_in_hr_zones,
        "target_time_in_power_zone": planned_time_in_power_zones,
        "target_time_in_hr_zone": planned_time_in_hr_zones,
        "ride_summary": ride_summary_dict,
        "cur_ftp": cur_ftp,
        "cur_fthr": cur_fthr,
        "profile_variable": profile_variable,
    }
    return session_details


def get_session_graph_data_dict(
    actual_power_data,
    planned_power_data,
    actual_hr_data,
    planned_hr_data,
    is_ftp_available,
    is_fthr_available,
    is_power_meter_available,
):
    session_details = {
        "actual_power_graph_data": actual_power_data,
        "actual_hr_graph_data": actual_hr_data,
        "target_power_graph_data": planned_power_data,
        "target_hr_graph_data": planned_hr_data,
        "is_ftp_available": is_ftp_available,
        "is_fthr_available": is_fthr_available,
        # Deprecated from R7
        "is_power_meter_available": is_power_meter_available,
    }
    return session_details


def get_session_details_dict_other_data(
    evaluation_scores,
    actual_time_in_power_zones_dict,
    actual_time_in_hr_zones_dict,
    planned_time_in_power_zones,
    planned_time_in_hr_zones,
    ride_summary_dict,
    is_power_meter_available,
    is_ftp_available,
    is_fthr_available,
    activity_info,
    is_ftp_input_needed,
    is_fthr_input_needed,
    session_date_time,
    planned_interval_data=None,
    actual_interval_data=None,
    zone_name=None,
    session_metadata=None,
    zone_focus=None,
    session_name=None,
    show_pairing_message=None,
    show_pairing_option=None,
    session_description=None,
    planned_duration=None,
    planned_intensity=None,
    effort_level=None,
    edit_manual_activity_data=None,
    accuracy_scores=None,
    key_zones=None,
    accuracy_score_overview=None,
    activity_label=None,
    key_zone_description=None,
    planned_session_name=None,
    power_zone_performance=None,
    heart_rate_zone_performance=None,
    warnings=None,
):
    """Returns session details which is shown in session evaluation page"""

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
        "show_pairing_message": show_pairing_message,
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
        "warnings": warnings,
        # Deprecated from R8
        "session_time": session_date_time,
        # Deprecated from R7
        "is_power_meter_available": is_power_meter_available,
    }
    return session_details


def iterate_data(user_data, total_point):
    interval = math.ceil(len(user_data) / total_point)
    data_count = 0
    total_value = 0
    for index, data in enumerate(user_data, start=1):
        total_value += data["value"]
        data_count += 1

        if index == 1 or data_count == interval:
            total_value = round(total_value / data_count)
            yield total_value, index

            total_value = 0
            data_count = 0


def get_power_data_dict_with_threshold(power_data, cur_ftp: int, total_point: int):
    power_data_dict_list = []
    for power_value, time_index in iterate_data(power_data, total_point):
        power_data_dict_list.append(
            {
                "time": time_index,
                "value": power_value,
                "zone_focus": CommonClass.get_zone_focus_from_power(
                    cur_ftp, power_value
                ),
            }
        )
    return power_data_dict_list


def get_hr_data_dict_with_threshold(
    hr_data, cur_fthr: int, max_hr: int, total_point: int
):

    hr_data_dict_list = []
    for hr_value, time_index in iterate_data(hr_data, total_point):
        if cur_fthr:
            zone_focus = CommonClass.get_zone_focus_from_hr(cur_fthr, hr_value)
        else:
            zone_focus = CommonClass.get_zone_focus_from_hr_by_max_hr(max_hr, hr_value)
        hr_data_dict_list.append(
            {"time": time_index, "value": hr_value, "zone_focus": zone_focus}
        )
    return hr_data_dict_list


def get_evaluation_scores_dict(
    actual_session, planned_session, evaluation_scores_comment
):
    evaluation_scores_dict_list = [
        {
            "name": "PSS",
            "unit": "",
            "score": int(
                actual_session.session_score.pss_score if actual_session else 0
            ),
            "target": round(planned_session.planned_pss),
            "actual": round(actual_session.actual_pss if actual_session else 0),
            "comment": evaluation_scores_comment["pss_score_comment"],
        },
        {
            "name": "Duration",
            "unit": "min",
            "score": int(
                actual_session.session_score.duration_score if actual_session else 0
            ),
            "target": int(planned_session.planned_duration),
            "actual": int(actual_session.actual_duration if actual_session else 0),
            "comment": evaluation_scores_comment["duration_score_comment"],
        },
        {
            "name": "Intensity",
            "unit": "%",
            "score": int(
                actual_session.session_score.sqs_session_score if actual_session else 0
            ),
            "target": round(planned_session.planned_intensity * 100),
            "actual": int(
                actual_session.actual_intensity * 100 if actual_session else 0
            ),
            "comment": evaluation_scores_comment["sqs_session_score_comment"],
        },
    ]

    return evaluation_scores_dict_list


def get_accuracy_scores_dict(
    actual_session,
    planned_session,
    accuracy_scores_comment,
    actual_time_in_key_zones: int,
    actual_time_in_non_key_zones: int,
    planned_time_in_key_zones: int,
    planned_time_in_non_key_zones: int,
):
    return [
        {
            "name": "Duration",
            "unit": "mins",
            "score": int(
                actual_session.session_score.duration_accuracy_score
                if actual_session
                else 0
            ),
            "target": int(planned_session.planned_duration),
            "actual": int(actual_session.actual_duration if actual_session else 0),
            "comment": accuracy_scores_comment["duration_score_comment"],
        },
        {
            "name": "Time in key zones",
            "unit": "mins",
            "score": int(
                actual_session.session_score.key_zone_score if actual_session else 0
            ),
            "target": int(planned_time_in_key_zones // 60),  # Converted into minutes
            "actual": int(actual_time_in_key_zones // 60),
            "comment": accuracy_scores_comment["key_zone_score_comment"],
        },
        {
            "name": "Time in non-key zones",
            "unit": "mins",
            "score": int(
                actual_session.session_score.non_key_zone_score if actual_session else 0
            ),
            "target": int(planned_time_in_non_key_zones // 60),
            "actual": int(actual_time_in_non_key_zones // 60),
            "comment": accuracy_scores_comment["non_key_zone_score_comment"],
        },
        {
            "name": "Intensity",
            "unit": "%",
            "score": int(
                actual_session.session_score.intensity_accuracy_score
                if actual_session
                else 0
            ),
            "target": round(planned_session.planned_intensity * 100),
            "actual": int(
                actual_session.actual_intensity * 100 if actual_session else 0
            ),
            "comment": accuracy_scores_comment["intensity_score_comment"],
        },
    ]


def get_session_info_dict(
    moving_time,
    elapsed_time,
    distance,
    average_speed,
    elevation,
    intensity,
    pss,
    weighted_power,
):
    return [
        {
            "type": "Moving Time",
            "value": moving_time,
            "unit": "",
        },
        {
            "type": "Elapsed Time",
            "value": elapsed_time,
            "unit": "",
        },
        {
            "type": "Distance",
            "value": distance,
            "unit": "km",
        },
        {
            "type": "Average Speed",
            "value": average_speed,
            "unit": "km/h",
        },
        {
            "type": "Elevation",
            "value": elevation,
            "unit": "m",
        },
        {
            "type": "Intensity",
            "value": intensity,
            "unit": "%",
        },
        {
            "type": "PSS",
            "value": pss,
            "unit": "PSS",
        },
        {
            "type": "Weighted Power",
            "value": weighted_power,
            "unit": "W",
        },
    ]
