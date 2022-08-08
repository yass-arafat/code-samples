import json
import logging
import os
from decimal import Decimal

import requests
from django.conf import settings
from fitparse import FitFile
from requests_oauthlib import OAuth1Session

from core.apps.activities.utils import dakghor_get_athlete_info
from core.apps.common.const import MAX_ACTIVITY_FILE_SIZE
from core.apps.common.enums.activity_data_type import ActivityDataTypeEnum

from .dictionary import (
    get_workout_steps_dict_for_garmin,
    initialize_send_workout_to_garmin_dict,
)

logger = logging.getLogger(__name__)
activity_files_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "activityfiles"
)


def read_activity_file(filename):
    activity_file_path = os.path.join(activity_files_path, filename)
    file_size = os.stat(activity_file_path).st_size
    if file_size > MAX_ACTIVITY_FILE_SIZE:
        logger.info(
            f"Fitfile: {filename} is a corrupt fit file. "
            f"The size of the file is greater than 5MB"
        )
        return None, True
    return FitFile(activity_file_path), False


def get_activity_file_datetime(fitfile_file_id):
    for records in fitfile_file_id:
        # Go through all the data entries in this record
        for record_data in records:
            if record_data.name == "time_created":
                activity_datetime = record_data.value
                return activity_datetime


def dakghor_get_athlete_garmin_permissions(user_code):
    url = settings.DAKGHOR_URL + "/api/v1/garmin/permissions"
    return requests.get(url=url, json={"athlete_code": user_code})


def get_step_intensity(session_interval_name):
    """Returns the garmin defined intensity type of a session interval"""
    if session_interval_name == "Warm Up":
        return "WARMUP"
    elif session_interval_name == "Warm Down":
        return "COOLDOWN"
    elif session_interval_name == "Recover":
        return "RECOVERY"
    else:
        return "INTERVAL"


def get_interval_target_values(ftp, fthr, data_type, session_interval):
    """Returns the target low and high values for a session interval or workout step"""
    target_value_low = None
    target_value_high = None
    if data_type == ActivityDataTypeEnum.POWER.value:
        if session_interval.ftp_percentage_lower:
            target_value_low = (
                Decimal(ftp) * session_interval.ftp_percentage_lower / Decimal(100.0)
            )
        if session_interval.ftp_percentage_upper:
            target_value_high = (
                Decimal(ftp) * session_interval.ftp_percentage_upper / Decimal(100.0)
            )
    elif data_type == ActivityDataTypeEnum.HEART_RATE.value:
        if session_interval.fthr_percentage_lower:
            target_value_low = (
                Decimal(fthr) * session_interval.fthr_percentage_lower / Decimal(100.0)
            )
        if session_interval.fthr_percentage_upper:
            target_value_high = (
                Decimal(fthr) * session_interval.fthr_percentage_upper / Decimal(100.0)
            )

    return target_value_low, target_value_high


def get_json_format_workout_for_garmin(
    workout_name, data_type, ftp, fthr, planned_session
):
    """Formats a session into json for sending a workout to Garmin"""
    workout = initialize_send_workout_to_garmin_dict(
        workout_name, planned_session.session
    )
    workout_steps = get_workout_steps_dict_for_garmin(
        data_type, ftp, fthr, planned_session
    )
    workout.update({"steps": workout_steps})

    return workout


def make_send_workout_to_garmin_request(user, workout):
    """Makes a send Pillar workout request to Garmin and returns the response code"""

    client_key = settings.GARMIN_CONSUMER_KEY
    client_secret = settings.GARMIN_CONSUMER_SECRET
    user_info = dakghor_get_athlete_info(user.id)
    garmin_user_token = user_info["garmin_user_token"]
    garmin_user_secret = user_info["garmin_user_secret"]

    if not (garmin_user_token and garmin_user_secret):
        return 403, "User Garmin credentials weren't found"

    garmin = OAuth1Session(
        client_key=client_key,
        client_secret=client_secret,
        resource_owner_key=garmin_user_token,
        resource_owner_secret=garmin_user_secret,
    )

    url = "https://apis.garmin.com/training-api/workout"

    response = garmin.post(url, json=workout)
    if response.status_code == 200 or response.status_code == 204:
        msg = ""
    else:
        text = json.loads(response.text)
        msg = text["message"]
    return response.status_code, msg


def update_garmin_permissions(user):
    """Sends request to dakghor for updating the Garmin permissions of user"""
    url = settings.DAKGHOR_URL + "/api/v1/garmin/update-garmin-permissions-task"
    response = requests.post(url=url, json={"user_id": user.id})
    return response.json()
