def get_performance_overview_dict(
    title="",
    weekly_distance="",
    weekly_duration=0,
    weekly_elevation="",
    current_freshness=0,
):
    return {
        "title": title,
        "weekly_distance": weekly_distance,
        "weekly_duration": weekly_duration,
        "weekly_elevation": weekly_elevation,
        "current_freshness": current_freshness,
    }


def get_performance_stats_dict(
    weekly_distance="", weekly_duration=0, weekly_elevation=""
):
    return {
        "weekly_distance": weekly_distance,
        "weekly_duration": weekly_duration,
        "weekly_elevation": weekly_elevation,
    }


def get_prs_overview_dict(
    current_prs=0,
    prs_score_remarks="",
    starting_prs=0,
    target_prs=0,
    average_session_accuracy_score=0,
):
    return {
        "current_prs": current_prs,
        "prs_score_remarks": prs_score_remarks,
        "starting_prs": starting_prs,
        "target_prs": target_prs,
        "average_session_accuracy_score": average_session_accuracy_score,
    }


def get_freshness_overview_dict(
    freshness_value=0, freshness_title="", freshness_remarks=""
):
    return {
        "freshness_value": freshness_value,
        "freshness_title": freshness_title,
        "freshness_remarks": freshness_remarks,
    }


def get_training_load_overview_dict(load_title="", load_remarks=""):
    return {"load_title": load_title, "load_remarks": load_remarks}


def get_threshold_overview_dict(
    current_ftp=None,
    current_fthr=None,
    threshold_remarks="",
    custom_graph_start_date=None,
):
    return {
        "current_ftp": current_ftp,
        "current_fthr": current_fthr,
        "threshold_remarks": threshold_remarks,
        "custom_graph_start_date": custom_graph_start_date,
    }
