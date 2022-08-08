from core.apps.common.const import MIN_STARTING_LOAD


def get_pss_week(pss_week_model):
    pss_week = (
        pss_week_model.const1
        * pss_week_model.hours_week
        * (pss_week_model.intensity_const**2)
    )
    return pss_week


def get_starting_user_load(starting_load_model):
    starting_load = (
        starting_load_model.pss_daily_week1
        + starting_load_model.pss_daily_week2
        + starting_load_model.pss_daily_week3
        + starting_load_model.pss_daily_week4
    ) / 4
    return max(MIN_STARTING_LOAD, starting_load)
