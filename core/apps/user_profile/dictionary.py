from core.apps.common.dictionary.training_zone_dictionary import (
    training_zone_truth_table_dict,
)
from core.apps.common.utils import get_traffic_light_info


def get_athletes_dict_for_coach_portal_dashboard(
    user_id,
    user_profile,
    user_personalise_data,
    rides_completed,
    rides_total,
    days_due_of_event,
    profile_picture_url,
    actual_day_data,
    is_placeholder_image,
    profile_image_url,
):
    cur_freshness = (
        round(actual_day_data.actual_load - actual_day_data.actual_acute_load, 1)
        if actual_day_data
        else 0
    )
    color, description = get_traffic_light_info(cur_freshness)
    athletes_dict = {
        "id": user_id,
        "full_name": user_profile.name
        + ("" if user_profile.surname is None else user_profile.surname),
        "age": user_personalise_data.get_age(),
        "profile_picture_url": profile_picture_url,
        "zone_focus_name": training_zone_truth_table_dict[actual_day_data.zone_focus][
            "zone_name"
        ]
        if actual_day_data
        else None,
        "current_prs": int(actual_day_data.prs_score) if actual_day_data else 0,
        "rides_completed": rides_completed,
        "rides_total": rides_total,
        "current_freshness": str(cur_freshness),
        "freshness_zone_color": color,
        "freshness_zone_description": description,
        "days_due_of_event": days_due_of_event,
        "is_placeholder_image": is_placeholder_image,
        "profile_image_url": profile_image_url,
    }
    return athletes_dict
