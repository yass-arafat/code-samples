def get_daily_prs_dictionary(
    daily_actual_prs,
    daily_target_prs,
    goal_status,
    event_date,
    event_name,
    event_distance,
):
    daily_prs_dict = {
        "actual_prs_graph_data": daily_actual_prs,
        "target_prs_graph_data": daily_target_prs,
        "goal_status": goal_status,
        "event_date": event_date,
        "event_name": event_name,
        "event_distance": event_distance,
    }
    return daily_prs_dict


def get_load_graph_dictionary(daily_actual_load_list, load_today, today_date):
    load_graph_dictionary = {
        "target_load_graph_data": daily_actual_load_list,
        "today_load": load_today,
        "today_date": today_date,
    }
    return load_graph_dictionary


def get_seven_days_ri_dict(data):
    ri_dict = {"actual_recovery_index_graph_data": data}
    return ri_dict


def get_seven_days_sqs_dict(data):
    sqs_dict = {"actual_sqs_graph_data": data}
    return sqs_dict
