from core.apps.event.enums.sports_type_enum import SportsTypeEnum


def get_plan_overview_dictionary(
    goal_name="",
    sports_type=SportsTypeEnum.CYCLING.value,
    sessions_completed=0,
    sessions_remaining=0,
    goal_type=None,
    package_type=None,
    days_till_goal_complete=0,
    has_goal=False,
):
    return {
        "goal_name": goal_name,
        "goal_type": goal_type,
        "package_type": package_type,
        "sports_type": sports_type,
        "sessions_completed": sessions_completed,
        "sessions_remaining": sessions_remaining,
        "days_till_goal_complete": days_till_goal_complete,
        "has_goal": has_goal,
        "event_name": goal_name,  # Deprecated from R13
        "days_till_event": days_till_goal_complete,  # Deprecated from R13
    }


def get_plan_stats_dictionary(
    sports_type=SportsTypeEnum.CYCLING.value,
    has_goal=False,
    sessions_completed=0,
    sessions_remaining=0,
    performance_goal=None,
    goal_progress_percentage=0,
    previous_goal_completed=False,
    goal_name="",
    days_till_goal_complete=0,
    goal_date=None,
):
    return {
        "goal_name": goal_name,
        "sports_type": sports_type,
        "sessions_completed": sessions_completed,
        "sessions_remaining": sessions_remaining,
        "days_till_goal_complete": days_till_goal_complete,
        "has_goal": has_goal,
        "previous_goal_completed": previous_goal_completed,
        "goal_date": goal_date,
        "performance_goal": performance_goal,
        "goal_progress_percentage": goal_progress_percentage,
        "event_name": goal_name,  # Deprecated from R13
        "days_till_event": days_till_goal_complete,  # Deprecated from R13
        "event_date": goal_date,  # Deprecated from R13
    }


def get_event_details_dictionary(
    goal_name="",
    sports_type=SportsTypeEnum.CYCLING.value,
    goal_date=None,
    sessions_completed=0,
    sessions_remaining=0,
    days_till_goal_complete=0,
    event_venue=None,
    goal_progress_percentage=0,
    event_elevation=0,
    event_distance=0,
    event_duration_in_days=1,
):
    return {
        "goal_name": goal_name,
        "sports_type": sports_type,
        "sessions_completed": sessions_completed,
        "sessions_remaining": sessions_remaining,
        "days_till_goal_complete": days_till_goal_complete,
        "goal_date": goal_date,
        "event_venue": event_venue,
        "goal_progress_percentage": goal_progress_percentage,
        "event_elevation": event_elevation,
        "event_distance": event_distance,
        "event_duration_in_days": event_duration_in_days,
        "event_name": goal_name,  # Deprecated from R13
        "days_till_event": days_till_goal_complete,  # Deprecated from R13
        "event_date": goal_date,  # Deprecated from R13
    }


def get_package_details_dictionary(
    goal_name=None,
    sports_type=SportsTypeEnum.CYCLING.value,
    goal_date=None,
    sessions_completed=0,
    sessions_remaining=0,
    days_till_goal_complete=0,
    goal_progress_percentage=0,
    package_duration=0,
    sub_package_name=None,
    sub_package_icon_url=None,
    sub_package_description=None,
    knowledge_hub_title=None,
    knowledge_hub_description=None,
    package_id=None,
    image_url=None,
):
    return {
        "goal_name": goal_name,
        "sports_type": sports_type,
        "sessions_completed": sessions_completed,
        "sessions_remaining": sessions_remaining,
        "days_till_goal_complete": days_till_goal_complete,
        "goal_date": goal_date,
        "goal_progress_percentage": goal_progress_percentage,
        "package_duration": f"{round(package_duration / 7)} weeks",
        "sub_package_name": sub_package_name,
        "sub_package_icon_url": sub_package_icon_url,
        "sub_package_description": sub_package_description,
        "knowledge_hub_title": knowledge_hub_title,
        "knowledge_hub_description": knowledge_hub_description,
        "package_id": package_id,
        "image_url": image_url,
    }
