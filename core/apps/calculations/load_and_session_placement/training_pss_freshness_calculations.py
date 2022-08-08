from core.apps.common.common_functions import (
    get_acute_load_start_for_user,
    get_load_start_for_user,
    get_yesterday,
)
from core.apps.common.const import MINIMUM_FRESHNESS


def get_training_pss_freshness(training_pss_freshness_model):
    yesterday = get_yesterday(training_pss_freshness_model.day)
    user = training_pss_freshness_model.day.user_auth
    load_start = get_load_start_for_user(user)
    acute_load_start = get_acute_load_start_for_user(user)
    lambda_load = training_pss_freshness_model.lambda_load
    lambda_acute_load = training_pss_freshness_model.lambda_acute_load

    pss_commute = training_pss_freshness_model.day.commute_pss_day
    if yesterday:
        previous_acute_load = yesterday.planned_acute_load
        previous_load = yesterday.planned_load
    else:
        previous_acute_load = acute_load_start
        previous_load = load_start

    training_pss_freshness = (
        (
            MINIMUM_FRESHNESS
            - (lambda_load * previous_load)
            + (lambda_acute_load * previous_acute_load)
        )
        / (lambda_acute_load - lambda_load)
    ) - pss_commute

    return training_pss_freshness
