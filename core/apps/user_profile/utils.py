import logging

import requests

from core.apps.common.enums.activity_data_type import ActivityDataTypeEnum
from core.apps.common.utils import (
    create_new_model_instance,
    get_headers,
    get_max_heart_rate_from_age,
    log_extra_fields,
)

from ..activities.utils import daroan_get_athlete_info
from ..common.date_time_utils import convert_str_date_time_to_date_time_obj
from ..common.enums.service_enum import ServiceType
from ..common.enums.trainer_urls import TrainerURLEnum
from .enums.user_access_level_enum import UserAccessLevelEnum
from .models import UserPersonaliseData

logger = logging.getLogger(__name__)


def get_user_ftp(user_auth, activity_datetime):
    ftp_filtered_data = user_auth.personalise_data.filter(
        current_ftp__isnull=False, current_ftp__gt=0
    )

    user_personalise_obj = (
        ftp_filtered_data.filter(created_at__date__lte=activity_datetime.date()).last()
        or ftp_filtered_data.first()
    )
    return user_personalise_obj.current_ftp if user_personalise_obj else 0


def get_user_fthr(user_auth, activity_datetime):
    fthr_filtered_data = user_auth.personalise_data.filter(
        current_fthr__isnull=False, current_fthr__gt=0
    )

    user_personalise_obj = (
        fthr_filtered_data.filter(created_at__date__lte=activity_datetime.date()).last()
        or fthr_filtered_data.first()
    )
    return user_personalise_obj.current_fthr if user_personalise_obj else 0


def get_user_max_heart_rate(user_auth, activity_datetime):
    mhr_filtered_data = user_auth.personalise_data.filter(
        max_heart_rate__isnull=False, max_heart_rate__gt=0
    )

    user_personalise_obj = (
        mhr_filtered_data.filter(created_at__date__lte=activity_datetime.date()).last()
        or mhr_filtered_data.first()
    )
    if user_personalise_obj:
        return user_personalise_obj.max_heart_rate

    user_personalise_obj = user_auth.personalise_data.filter(is_active=True).last()
    if user_personalise_obj:
        return get_max_heart_rate_from_age(user_personalise_obj.date_of_birth)
    return None


def get_user_weight(user_auth, activity_datetime):
    weight_filtered_data = user_auth.personalise_data.filter(
        weight__isnull=False, weight__gt=0
    )

    user_personalise_obj = (
        weight_filtered_data.filter(
            created_at__date__lte=activity_datetime.date()
        ).last()
        or weight_filtered_data.first()
    )
    return user_personalise_obj.weight if user_personalise_obj else None


def get_user_gender(user_auth, activity_datetime):
    gender_filtered_data = user_auth.profile_data.filter(gender__isnull=False)

    user_profile_obj = (
        gender_filtered_data.filter(
            created_at__date__lte=activity_datetime.date()
        ).last()
        or gender_filtered_data.first()
    )
    return user_profile_obj.gender if user_profile_obj else None


def get_user_age(user_auth, activity_datetime):
    user_personalise_obj = UserPersonaliseData.objects.filter(
        user_auth=user_auth, is_active=True
    ).last()
    return (
        user_personalise_obj.get_age(current_date=activity_datetime)
        if user_personalise_obj
        else None
    )


def update_user_baseline_fitness(
    baseline_fitness_data, user, user_personalise_data=None
):
    current_ftp = baseline_fitness_data.get("current_ftp", False)
    current_fthr = baseline_fitness_data.get("current_threshold_heart_rate", False)
    max_heart_rate = baseline_fitness_data.get("max_heart_rate", False)

    if user_personalise_data is None:
        user_personalise_data = user.personalise_data.filter(is_active=True).last()

    if (
        current_ftp == user_personalise_data.current_ftp
        and current_fthr == user_personalise_data.current_fthr
        and max_heart_rate == user_personalise_data.max_heart_rate
    ):
        return

    if current_ftp:
        user_personalise_data.current_ftp = current_ftp
    if current_fthr:
        user_personalise_data.current_fthr = current_fthr
    if max_heart_rate:
        user_personalise_data.max_heart_rate = max_heart_rate

    user_personalise_data = create_new_model_instance(user_personalise_data)
    user_personalise_data.save()


def update_user_baseline_fitness_request(user, request):
    ftp_input_denied = request.data.get("ftp_input_denied", False)
    fthr_input_denied = request.data.get("fthr_input_denied", False)
    # user_personalise_data = user.personalise_data.filter(is_active=True).last()
    user_personalise_data = UserPersonaliseData.objects.filter(
        user_id=user.code, is_active=True
    ).last()

    if ftp_input_denied and not user_personalise_data.ftp_input_denied:
        user_personalise_data.ftp_input_denied = True
        user_personalise_data = create_new_model_instance(user_personalise_data)
        user_personalise_data.save()
    elif fthr_input_denied and not user_personalise_data.fthr_input_denied:
        user_personalise_data.fthr_input_denied = True
        user_personalise_data = create_new_model_instance(user_personalise_data)
        user_personalise_data.save()
    else:
        baseline_fitness_data = request.data.get("baseline_fitness", False)
        if baseline_fitness_data:
            update_user_baseline_fitness(
                baseline_fitness_data, user, user_personalise_data
            )
            session_metadata = request.data.get("session_metadata", False)
            if session_metadata:
                """This code consists bug and Need refactor ASAP
                write two api's, one in dakghor and one in trainer
                to recalculate files from this day to current day. untill
                those functions are ready, blocking this line"""
                # actual_session = recalculate_single_session(
                #     user, session_metadata["actual_id"]
                # )
                # session_metadata["actual_id"] = actual_session.id
                return session_metadata
    return None


def update_user_threshold_value(user, data_type, input_ftp, input_fthr):
    """
    Updates the threshold values of a user (FTP, FTHR) according to the new inputs
    during the send workout to Garmin process
    """
    user_personalise_data = user.personalise_data.filter(is_active=True).last()

    if (
        data_type == ActivityDataTypeEnum.POWER.value
        and user_personalise_data.current_ftp != input_ftp
    ):
        user_personalise_data.current_ftp = input_ftp
        user_personalise_data.save()

    if (
        data_type == ActivityDataTypeEnum.HEART_RATE.value
        and user_personalise_data.current_fthr != input_fthr
    ):
        user_personalise_data.current_fthr = input_fthr
        user_personalise_data.save()


def populate_user_access_level(user):
    """Populates the access level of user profile table for every user"""
    user_profile = user.profile_data.filter(is_active=True).last()
    if user_profile and user.user_plans.exists():
        user_profile.access_level = UserAccessLevelEnum.HOME.value[0]
        user_profile.save(update_fields=["access_level"])


def split_user_name(name):
    name = name.strip()
    if len(name.split()) > 1:
        name, surname = name.rsplit(" ", 1)
        name = name.strip()
        surname = surname.strip()
        return name, surname
    return name, ""


def calculate_morning_data(payload, user_id):
    url = TrainerURLEnum.CALCULATE_MORNING_DATA.value
    logger.info(f"Calculating morning data {url}")
    headers = get_headers(user_id=user_id)
    response = requests.post(url=url, json=payload, headers=headers)

    logger.info(f"response {response}")
    if response.status_code != 200:
        logger.exception(
            f"Error when running morning calculation for user {response.status_code}",
            extra=log_extra_fields(
                user_id=user_id,
                service_type=ServiceType.API.value,
            ),
        )


def get_user_starting_values(user_id):
    user_personalize_data = UserPersonaliseData.objects.filter(user_id=user_id).first()
    athelete_info = daroan_get_athlete_info(user_id)["data"]
    if not athelete_info:
        logger.error(f"Starting value API: No info from daroan for user: {user_id}")
        onboarding_date = None
    else:
        onboarding_date = convert_str_date_time_to_date_time_obj(
            athelete_info["joining_date"]
        ).date()

    return {
        "onboarding_date": onboarding_date,
        "starting_load": user_personalize_data.starting_load,
        "starting_acute_load": user_personalize_data.starting_acute_load,
    }


def clear_trainer_cache(user_id):
    logger.info("Resetting user data and clearing the cache from trainer")
    headers = get_headers(user_id=user_id)
    response = requests.get(
        url=TrainerURLEnum.CLEAR_CACHE.value,
        headers=headers,
    )
    logger.info(f"status code {response.status_code}")
    if response.status_code != 200:
        raise ValueError("Internal Server error when fetching data from trainer")
