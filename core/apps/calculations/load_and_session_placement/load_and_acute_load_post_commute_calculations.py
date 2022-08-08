from core.apps.common.common_functions import (
    get_acute_load_start_for_user,
    get_load_start_for_user,
    get_yesterday,
)


def get_load_post_commute(load_post_commute_model):
    """Calculate and return load post commute"""

    yesterday = get_yesterday(load_post_commute_model.day)
    if yesterday:
        previous_planned_load = yesterday.planned_load
    else:
        previous_planned_load = get_load_start_for_user(
            load_post_commute_model.day.user_auth
        )

    load_post_commute = (
        load_post_commute_model.lambda_load * previous_planned_load
        + (1 - load_post_commute_model.lambda_load)
        * load_post_commute_model.day.commute_pss_day
    )
    return load_post_commute


def get_acute_load_post_commute(acute_load_post_commute_model):
    """Calculate and return load post commute"""

    yesterday = get_yesterday(acute_load_post_commute_model.day)
    if yesterday:
        previous_planned_acute_load = yesterday.planned_acute_load
    else:
        previous_planned_acute_load = get_acute_load_start_for_user(
            acute_load_post_commute_model.day.user_auth
        )

    acute_load_post_commute = (
        acute_load_post_commute_model.lambda_acute_load * previous_planned_acute_load
        + (1 - acute_load_post_commute_model.lambda_acute_load)
        * acute_load_post_commute_model.day.commute_pss_day
    )
    return acute_load_post_commute
