from core.apps.common.dictionary.training_zone_dictionary import (
    training_zone_truth_table_dict,
)


def get_athlete_profile_dict(
    user_id,
    user_profile,
    user_personalise_data,
    rides_completed,
    target_prs,
    days_due_of_event,
    profile_picture_url,
    actual_day_data,
    total_distance,
):
    athletes_dict = {
        "id": user_id,
        "profile_picture_url": profile_picture_url,
        "full_name": user_profile.name
        + ("" if user_profile.surname is None else user_profile.surname),
        "age": user_personalise_data.get_age(),
        "zone_focus_name": training_zone_truth_table_dict[actual_day_data.zone_focus][
            "zone_name"
        ],
        "starting_prs": int(user_personalise_data.starting_prs),
        "current_prs": int(actual_day_data.prs_score),
        "target_prs": int(target_prs),  # target_prs,
        "rides_completed": rides_completed,
        "total_distance": total_distance,
        "days_due_of_event": days_due_of_event,
    }
    return athletes_dict


def get_overview_dict(upcoming_rides_dict_arr, past_rides_dict_arr):
    overview_dict = {
        "upcoming_rides": upcoming_rides_dict_arr,
        "past_rides": past_rides_dict_arr,
    }

    return overview_dict
