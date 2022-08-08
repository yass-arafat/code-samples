import json
import logging
import os
import time
from collections import Counter
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from re import sub

import boto3
import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from log_request_id import local
from openpyxl import load_workbook

from core.apps.calculations.evaluation.recovery_index_services import (
    RecoveryIndexService,
)
from core.apps.user_profile.models import UserMetaData

from .const import (
    BACKFILL_REQUEST_DAY_LIMIT,
    HEART_RATE_UPPER_BOUNDARY_COEFFICIENT,
    MAX_HEART_RATE_FOR_PREDICTION,
    MAX_HR_TO_FTHR_COEFFICIENT,
    POWER_UPPER_BOUNDARY_COEFFICIENT,
    TEMPORARY_ACTIVITY_FILES_PATH,
    TIME_RANGE_BOUNDARY,
    TRAFFIC_LIGHT_THRESHOLD_VALUE,
)
from .enums.color import Color
from .enums.dakghor_urls_enum import DakghorURLEnum
from .enums.daroan_urls_enum import DaroanURLEnum
from .enums.date_time_format_enum import DateTimeFormatEnum
from .enums.traffic_light import TrafficLight
from .enums.treasury_urls_enum import TreasuryURLEnum
from .services import RoundServices

logger = logging.getLogger(__name__)


def make_context(error: bool = False, message: str = "", data=None):
    context = {"error": error, "message": message, "data": data}
    return context


def get_authorization_token_from_header(request):
    header = request.META.get("HTTP_AUTHORIZATION", None)
    logger.info(f"Header of the request {header}")
    if header is None:
        return None

    token = sub("Bearer ", "", request.META.get("HTTP_AUTHORIZATION", None))
    return token


def initialize_dict(start, end):
    return [{"zone": idx, "value": 0} for idx in range(start, end)]


def get_user_from_session_destroy_session_variable(request):
    from ..user_auth.models import UserAuthModel

    user_id = request.session["user_id"]
    user = UserAuthModel.objects.get_user(user_id)
    return user


def create_new_model_instance(model_object):
    model_object.is_active = False
    model_object.save(update_fields=["is_active", "updated_at"])
    model_object.pk = None
    model_object.is_active = True
    return model_object


def get_traffic_light_info(freshness):
    if freshness < (-TRAFFIC_LIGHT_THRESHOLD_VALUE):
        return Color.RED.value[0], TrafficLight.CONSIDERABLE_FATIGUE.value[0]
    elif (-TRAFFIC_LIGHT_THRESHOLD_VALUE) <= freshness < 0:
        return Color.ORANGE.value[0], TrafficLight.ACCUMULATING_FATIGUE.value[0]
    else:
        return Color.GREEN.value[0], TrafficLight.MINIMAL_FATIGUE.value[0]


def get_user_connected_table_instance(athlete_id, user_auth=None):
    from core.apps.user_auth.models import UserAuthModel

    if user_auth is None:
        user_auth = UserAuthModel.objects.filter(pk=athlete_id, is_active=True).first()
    user_profile = user_auth.profile_data.filter(is_active=True).first()
    user_personalise_data = user_auth.personalise_data.filter(is_active=True).first()
    user_event = user_auth.user_events.filter(is_active=True).last()

    return user_auth, user_profile, user_personalise_data, user_event


def is_recovery_day(zone_focus):
    """Zone Focus 0 represents Recovery Day for the athlete"""
    return not bool(zone_focus)


def get_activity_file_name(user_auth_id, file_extension):
    return str(user_auth_id) + "_" + str(time.time()).replace(".", "") + file_extension


def get_activity_file_s3_path(user_auth_id, upload_date, source, file_extension):
    activity_file_name = get_activity_file_name(user_auth_id, file_extension)
    return os.path.join(
        *[
            settings.HOST_SERVER,
            settings.ACTIVITYFILES_LOCATION,
            str(user_auth_id),
            source,
            str(upload_date.year),
            str(upload_date.month),
            str(upload_date.day),
            activity_file_name,
        ]
    )


def upload_file_to_s3(local_file_path, s3_file_path):
    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.upload_file(
        Filename=local_file_path,
        Bucket=settings.AWS_PRIVATE_STORAGE_BUCKET,
        Key=s3_file_path,
    )


def download_s3_file(s3_pillar_file_path):
    """Downloads file from S3 and returns path of the downloaded file"""
    Path(TEMPORARY_ACTIVITY_FILES_PATH).mkdir(parents=True, exist_ok=True)
    temporary_file_path = os.path.join(
        TEMPORARY_ACTIVITY_FILES_PATH, s3_pillar_file_path.split("/")[-1].strip()
    )
    if Path(temporary_file_path).exists():
        logger.info(f"File already exists. File name: {temporary_file_path}")
        return temporary_file_path

    s3 = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    s3.resource("s3", settings.AWS_S3_REGION_NAME).Bucket(
        settings.AWS_PRIVATE_STORAGE_BUCKET
    ).Object(s3_pillar_file_path).download_file(temporary_file_path)
    logger.info(f"File downloaded successfully. File name: {temporary_file_path}")
    return temporary_file_path


def read_s3_file(s3_pillar_file_path):
    """Returns binary data of the file from S3"""
    s3 = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    obj = (
        s3.resource("s3", settings.AWS_S3_REGION_NAME)
        .Bucket(settings.AWS_PRIVATE_STORAGE_BUCKET)
        .Object(s3_pillar_file_path)
        .get()
    )
    return obj["Body"].read()


def read_s3_xlsx_file(s3_pillar_file_path):
    binary_data = read_s3_file(s3_pillar_file_path)
    return load_workbook(BytesIO(binary_data)).active


def get_user_metadata(user_id):
    return UserMetaData.objects.filter(user_id=user_id, is_active=True).first()


def get_user_metadata_hash(user_id):
    user_metadata = get_user_metadata(user_id)
    return user_metadata.hash if user_metadata else None


def update_user_metadata_cache(user_id_list):
    timestamp = int(round(datetime.now().timestamp()))
    user_metadata_list = UserMetaData.objects.filter(
        user_id__in=user_id_list, is_active=True
    )
    logger.info(f"found {len(user_metadata_list)} user's meta data to update cache id")
    if len(user_metadata_list) > 0:
        for user_metadata in user_metadata_list:
            user_metadata.cache_id = timestamp
        UserMetaData.objects.bulk_update(user_metadata_list, ["cache_id"])


def get_power_upper_boundary(current_ftp):
    return round(POWER_UPPER_BOUNDARY_COEFFICIENT * current_ftp)


def get_heart_rate_upper_boundary(current_fthr):
    return round(HEART_RATE_UPPER_BOUNDARY_COEFFICIENT * current_fthr)


def get_freshness(chronic_load, acute_load):
    return chronic_load - acute_load


def get_rounded_freshness(actual_load, actual_acute_load):
    return RoundServices.round_freshness(get_freshness(actual_load, actual_acute_load))


def get_obj_recovery_index(obj):  # Parameter can be day or session
    # Freshness
    freshness = obj.actual_load - obj.actual_acute_load

    recovery_index_service = RecoveryIndexService(freshness)
    recovery_index = recovery_index_service.get_recovery_index()

    return recovery_index


def log_extra_fields(
    request_url=None,
    user_auth_id=None,
    user_id=None,
    service_type=None,
    exception_message=None,
):
    return {
        "exception": exception_message,
        "url": request_url,
        "user_auth_id": user_auth_id,
        "user_id": user_id,
        "service": service_type,
    }


def dakghor_connect_athlete(**request_body):
    url = DakghorURLEnum.THIRD_PARTY_CONNECT.value
    return requests.post(url=url, json=request_body)


def dakghor_disconnect_athlete(source, athlete_id):
    url = DakghorURLEnum.THIRD_PARTY_DISCONNECT.value
    request_body = {"source": source, "athlete_id": athlete_id}
    return requests.post(url=url, json=request_body)


def dakghor_backfill_request(source, athlete_id, start_time=None, end_time=None):
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=BACKFILL_REQUEST_DAY_LIMIT)

    url = settings.DAKGHOR_URL + "/api/v1/third-party/backfill"
    requests.post(
        url=url,
        json={
            "athlete_id": athlete_id,
            "start_time": start_time.strftime(DateTimeFormatEnum.app_date_format.value),
            "end_time": end_time.strftime(DateTimeFormatEnum.app_date_format.value),
            "source": source,
        },
    )


def dakghor_get_time_in_zones(athlete_activity_codes):
    if not athlete_activity_codes:
        return []
    url = DakghorURLEnum.TIME_IN_ZONE.value
    return requests.post(
        url=url, json={"athlete_activity_codes": athlete_activity_codes}
    ).json()["data"]["time_in_zone"]


def daroan_email_status(email):
    return requests.post(
        url=DaroanURLEnum.EMAIL_STATUS.value,
        json={
            "email": email,
            "authentication_secret_key": settings.DAROAN_API_SECRET_KEY,
        },
    ).json()["data"]


def daroan_reset_password(email, new_password):
    return requests.post(
        url=DaroanURLEnum.RESET_PASSWORD.value,
        headers={"Correlation-Id": local.request_id},
        json={"email": email, "password": new_password},
    )


def daroan_login(**request_body):
    logger.info("Calling daroan for login ....")
    return requests.post(url=DaroanURLEnum.LOGIN.value, json=request_body)


def daroan_refresh_token(refresh_token):
    if len(refresh_token) == 36:  # Length of uuid string is 36
        payload = {"refresh_token": refresh_token}
    else:
        payload = {"refresh_jwt_token": refresh_token}
    return requests.post(url=DaroanURLEnum.REFRESH.value, json=payload)


def daroan_register_user(**request_body):
    return requests.post(url=DaroanURLEnum.REGISTER.value, json=request_body)


def treasury_create_subscription(**request_body):
    return requests.post(
        url=TreasuryURLEnum.SUBSCRIPTION_CREATE.value, json=request_body
    )


def treasury_sync_subscription(**request_body):
    return requests.post(url=TreasuryURLEnum.SUBSCRIPTION_SYNC.value, json=request_body)


def daroan_validate_token(access_token: str):
    if len(access_token) == 36:  # Length of uuid string is 36
        payload = {"access_token": access_token}
    else:
        payload = {"access_jwt_token": access_token}
    payload.update({"authentication_secret_key": settings.DAROAN_API_SECRET_KEY})

    url = DaroanURLEnum.VALIDATE_TOKEN.value
    response = requests.post(url=url, json=payload)
    if response.status_code != 200:
        return None, None
    response_data = response.json()["data"]

    return response_data["code"], response_data["subscription_status"]


def get_duplicate_session_timerange(_datetime):
    start_time = _datetime - timedelta(seconds=TIME_RANGE_BOUNDARY)
    end_time = _datetime + timedelta(seconds=TIME_RANGE_BOUNDARY)
    return start_time, end_time


def get_ride_summary(ride_summary):
    selected_ride_summary = []
    if ride_summary:
        types = ["Heart Rate", "Power", "Speed", "Cadence"]
        decimal_places = {"Heart Rate": 0, "Power": 0, "Speed": 1, "Cadence": 0}
        ride_summaries = json.loads(ride_summary.replace("'", '"'))

        for summary in ride_summaries:
            if summary["type"] in types:
                if decimal_places[summary["type"]]:
                    summary["average"] = round(
                        summary["average"], decimal_places[summary["type"]]
                    )
                    summary["max"] = round(
                        summary["max"], decimal_places[summary["type"]]
                    )
                else:
                    summary["average"] = round(summary["average"])
                    summary["max"] = round(summary["max"])
                selected_ride_summary.append(summary)

    return selected_ride_summary


def get_ride_summary_v2(ride_summary):
    ride_summaries = get_ride_summary(ride_summary)
    for ride_summary in ride_summaries:
        ride_summary["average"] = (
            str(ride_summary["average"]) if ride_summary["average"] else None
        )
        ride_summary["max"] = str(ride_summary["max"]) if ride_summary["max"] else None
    return ride_summaries


def update_is_active_value(objects, is_active, reason=None):
    """
    Updates the is_active field of the objects of a object list.
    :param reason: The reason of deactivating the objects
    :param objects: The queryset whose objects need to be updated
    :param is_active: The updated is_active value
    """
    for obj in objects:
        obj.is_active = is_active
        if reason:
            obj.reason = reason
        obj.save()


def get_max_heart_rate_from_age(date_of_birth):
    """Predicts the max heart rate from current age"""

    user_age = get_user_age(date_of_birth)
    max_heart_rate = MAX_HEART_RATE_FOR_PREDICTION - user_age
    return max_heart_rate


def get_fthr_from_max_heart_rate(max_heart_rate):
    if max_heart_rate is None:
        return None
    return round(MAX_HR_TO_FTHR_COEFFICIENT * max_heart_rate)


def get_user_age(date_of_birth, current_date=None):
    if not current_date:
        current_date = date.today()
    user_age = (
        current_date.year
        - date_of_birth.year
        - (
            (current_date.month, current_date.day)
            < (date_of_birth.month, date_of_birth.day)
        )
    )
    return user_age


def cached_data(force_refresh, cache_key: str):

    if (lambda x, y: x != "true" and y in cache)(force_refresh, cache_key):
        return cache.get(cache_key)


def most_common_item_in_list(lst: list):
    """
    Returns the most common item in list.
    Returns the first most common element in case of ties. Returns None in case of error
    """
    data = Counter(lst)
    try:
        return max(lst, key=data.get)
    except ValueError:
        return None


def get_local_request_id():
    try:
        return local.request_id
    except Exception as e:
        logger.warning(str(e))


def get_headers(user_id=None):
    headers = {}
    if user_id:
        headers["User-Id"] = str(user_id)

    local_request_id = get_local_request_id()
    if local_request_id:
        headers["Correlation-Id"] = local_request_id

    return headers


def get_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise PermissionDenied("User id not found. Permission denied")
    return user_id
