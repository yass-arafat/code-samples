from core.apps.common.common_functions import get_load_start_for_user, get_yesterday


def get_training_pss_load(training_pss_load_model):
    yesterday = get_yesterday(training_pss_load_model.day)
    user = training_pss_load_model.day.user_auth
    if yesterday:
        training_pss_load = (
            training_pss_load_model.max_load
            - yesterday.planned_load * training_pss_load_model.lambda_load
        ) / (
            1 - training_pss_load_model.lambda_load
        ) - training_pss_load_model.day.commute_pss_day
    else:
        training_pss_load = (
            training_pss_load_model.max_load
            - get_load_start_for_user(user) * training_pss_load_model.lambda_load
        ) / (
            1 - training_pss_load_model.lambda_load
        ) - training_pss_load_model.day.commute_pss_day

    return training_pss_load
