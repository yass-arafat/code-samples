def get_commute_pss_of_week(commute_pss_model):
    commute_pss_of_week = (
        commute_pss_model.constant1
        * commute_pss_model.time_commute_in_hours
        * (commute_pss_model.intensity_commute_constant**2)
        * commute_pss_model.constant2
    )
    return commute_pss_of_week


def get_commute_pss_of_day(week, day):
    week_commute_pss = week.commute_pss_week
    user_auth = week.user_block.user_auth
    commute_days_array = user_auth.schedule_data.days_commute_by_bike[1:-1].split(",")
    week_day_no = day.date.weekday()

    if commute_days_array[week_day_no].strip().lower() == "false":
        return 0
    else:
        return week_commute_pss
