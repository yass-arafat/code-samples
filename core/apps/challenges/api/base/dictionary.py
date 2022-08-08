from decimal import Decimal

from core.apps.challenges.models import UserChallenge


def create_challenge_tile_dict(challenge):
    return {
        "challenge_metadata": {
            "challenge_id": challenge["id"],
            "challenge_taken": False,
        },
        "title": challenge["title"],
        "badge_url": challenge["badge_url"],
        "summary": challenge["summary"],
        "end_date": challenge["end_date"].strftime("%a, %-d %b %Y"),
    }


def create_user_challenge_dict(current_challenge):
    completion_percentage = 0.0
    challenge = current_challenge.challenge
    target_value = challenge.target_value
    achieved_value = (
        current_challenge.achieved_value if current_challenge.achieved_value else 0
    )
    if target_value and achieved_value:
        completion_percentage = achieved_value / (
            target_value * 1000
        )  # Convert target value from kilometer from meter

    return {
        "challenge_metadata": {
            "challenge_id": current_challenge.id,
            "challenge_taken": True,
            "is_completed": current_challenge.is_completed,
        },
        "title": challenge.title,
        "badge_url": challenge.badge_url,
        "summary": str(round(achieved_value / Decimal(1000.0)))
        + " "
        + challenge.unit
        + " of "
        + str(round(target_value))
        + " "
        + challenge.unit,
        "completion_percentage": completion_percentage
        if completion_percentage <= 1.0
        else 1.0,
        "end_date": challenge.end_date.strftime("%a, %-d %b %Y"),
    }


def user_challenge_details_dict(current_challenge, challenge):
    completion_percentage = 0.0
    target_value = challenge.target_value
    achieved_value = (
        current_challenge.achieved_value if current_challenge.achieved_value else 0
    )
    if target_value and achieved_value:
        completion_percentage = achieved_value / (
            target_value * 1000
        )  # Convert target value from kilometer from meter

    return {
        "challenge_metadata": {
            "challenge_id": current_challenge.id,
            "challenge_taken": True,
            "is_completed": current_challenge.is_completed,
        },
        "title": challenge.title,
        "summary": str(round(achieved_value / Decimal(1000.0)))
        + " "
        + challenge.unit
        + " of "
        + str(round(target_value))
        + " "
        + challenge.unit,
        "badge_url": challenge.badge_url,
        "background_image_url": challenge.image_url,
        "shareable_link": challenge.share_link,
        "description": challenge.description,
        "completion_percentage": completion_percentage
        if completion_percentage <= 1.0
        else 1.0,
        "end_date": challenge.end_date.strftime("%a, %-d %b %Y")
        if completion_percentage <= 1.0
        else "Challenge Finished",
    }


def is_challange_takable(challenge, user):
    # For share option, if a challenge is already taken or challenge date has been
    # passed then can't take this challenge.
    user_local_date = user.user_local_date
    user_challenge = UserChallenge.objects.filter(
        user_auth=user,
        is_active=True,
        challenge__start_date__lte=user_local_date,
        challenge__end_date__gte=user_local_date,
    ).last()
    return not bool(
        user_challenge
        or user_local_date < challenge.start_date
        or user_local_date > challenge.end_date
    )


def create_challenge_description_dict(challenge, user):
    return {
        "title": challenge.title,
        "badge_url": challenge.badge_url,
        "background_image_url": challenge.image_url,
        "description": challenge.description,
        "shareable_link": challenge.share_link,
        "end_date": challenge.end_date.strftime("%a, %-d %b %Y"),
        "is_takable": is_challange_takable(challenge, user),
    }


def create_challenge_progress_dict(
    week_no, week_start_date, week_end_date, week_distance, unit
):
    if not week_distance:
        week_distance = 0
    start_date = week_start_date.strftime("%d %b")
    end_date = week_end_date.strftime("%d %b")

    return {
        "interval_no": "Week " + str(week_no),
        "timeframe": str(start_date) + " - " + str(end_date),
        "value": str(round(week_distance / Decimal(1000.0))) + " " + unit,
    }


def get_achieved_trophy_dict(achieved_challenge):
    return {
        "badge": achieved_challenge["challenge__badge_url"],
        "name": achieved_challenge["challenge__title"],
        "date_time": achieved_challenge["completion_date"],
        "value": str(round(achieved_challenge["challenge__target_value"]))
        + " "
        + achieved_challenge["challenge__unit"],
    }
