from core.apps.common.common_functions import get_load_start_for_user, get_yesterday


def get_training_pss_max_ride(training_pss_max_ride_model):
    user = training_pss_max_ride_model.day.user_auth
    yesterday = get_yesterday(training_pss_max_ride_model.day)
    if yesterday:
        training_pss_max_ride = (
            training_pss_max_ride_model.const_max_single_ride_multiplier
            * yesterday.planned_load
            - training_pss_max_ride_model.pss_commute_nth_day
        )
    else:
        load_start = get_load_start_for_user(user)
        training_pss_max_ride = (
            training_pss_max_ride_model.const_max_single_ride_multiplier * load_start
            - training_pss_max_ride_model.pss_commute_nth_day
        )
    return training_pss_max_ride
