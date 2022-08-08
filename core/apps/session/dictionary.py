def get_session_graph_data_dict(session_graph_data_list):
    graph_data_dict_list = []
    time = 1
    for data in session_graph_data_list:
        graph_data_dict_list.append(
            {"value": data["value"], "zone_focus": data["zone_focus"]}
        )
        time += 1
    return graph_data_dict_list


USER_AWAY_REASONS = [
    "Work",
    "Personal Occasion",
    "Illness or Injury",
    "Holiday",
    "Broken equipment",
    "Weather",
    "Other",
]
