import json
import logging
import os
import time
from datetime import date, datetime
from uuid import UUID

import boto3
import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from rest_framework.exceptions import ValidationError

from config.emails import user_support_mail
from core.apps.activities.utils import daroan_get_athlete_info
from core.apps.common.common_functions import CommonClass, format_timezone
from core.apps.common.const import (
    FTHR_BOUNDARY,
    FTP_BOUNDARY,
    MAX_HR_BOUNDARY,
    MIN_STARTING_LOAD,
    UTC_TIMEZONE,
)
from core.apps.common.date_time_utils import (
    DateTimeUtils,
    convert_str_date_time_to_date_time_obj,
    convert_str_date_to_date_obj,
    daterange,
)
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    create_new_model_instance,
    get_max_heart_rate_from_age,
    log_extra_fields,
    make_context,
)
from core.apps.user_profile.api.versioned.v2.dictionary import timezone_dict
from core.apps.user_profile.enums.gender_enum import GenderEnum
from core.apps.user_profile.enums.user_access_level_enum import UserAccessLevelEnum
from core.apps.user_profile.enums.user_unit_system_enum import UserUnitSystemEnum
from core.apps.user_profile.models import (
    TimeZone,
    UserPersonaliseData,
    UserProfile,
    ZoneDifficultyLevel,
)
from core.apps.user_profile.services import get_user_starting_load_v2
from core.apps.user_profile.utils import calculate_morning_data, split_user_name

logger = logging.getLogger(__name__)


class UserProfileServiceV2:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.user_personalise_data_list = None
        self.is_profile_data_fields_updated = False
        self.is_personalise_data_fields_updated = False

    def _get_user_profile_data(self):
        logger.info("Fetching user profile data from db")
        try:
            return UserProfile.objects.filter(
                user_id=self.user_id, is_active=True
            ).first()
        except UserProfile.DoesNotExist:
            logger.exception(
                "No user found with given user id",
                extra=log_extra_fields(
                    user_id=self.user_id, service_type=ServiceType.API.value
                ),
            )

    def _get_user_personalise_data(self):
        logger.info("Fetching user personalise data from db")
        try:
            return UserPersonaliseData.objects.filter(
                user_id=self.user_id, is_active=True
            ).first()
        except UserPersonaliseData.DoesNotExist:
            logger.exception(
                "No user found with given user id",
                extra=log_extra_fields(
                    user_id=self.user_id, service_type=ServiceType.API.value
                ),
            )

    def _get_user_personalise_data_list(self):
        logger.info("Fetching user personalise data list from db")
        try:
            return UserPersonaliseData.objects.filter(user_id=self.user_id).all()
        except UserPersonaliseData.DoesNotExist:
            logger.exception(
                "No personalise data found with given user id",
                extra=log_extra_fields(
                    user_id=self.user_id, service_type=ServiceType.API.value
                ),
            )

    def _get_user_ftp(self, activity_datetime):
        ftp_filtered_data = self.user_personalise_data_list.filter(
            current_ftp__isnull=False, current_ftp__gt=0
        )

        user_personalise_obj = (
            ftp_filtered_data.filter(
                created_at__date__lte=activity_datetime.date()
            ).last()
            or ftp_filtered_data.first()
        )
        return user_personalise_obj.current_ftp if user_personalise_obj else None

    def _get_user_fthr(self, activity_datetime):
        fthr_filtered_data = self.user_personalise_data_list.filter(
            current_fthr__isnull=False, current_fthr__gt=0
        )

        user_personalise_obj = (
            fthr_filtered_data.filter(
                created_at__date__lte=activity_datetime.date()
            ).last()
            or fthr_filtered_data.first()
        )
        return user_personalise_obj.current_fthr if user_personalise_obj else None

    def _get_user_max_heart_rate(self, activity_datetime):
        mhr_filtered_data = self.user_personalise_data_list.filter(
            max_heart_rate__isnull=False, max_heart_rate__gt=0
        )

        user_personalise_obj = (
            mhr_filtered_data.filter(
                created_at__date__lte=activity_datetime.date()
            ).last()
            or mhr_filtered_data.first()
        )
        if user_personalise_obj:
            return user_personalise_obj.max_heart_rate

        user_personalise_obj = self.user_personalise_data_list.filter(
            is_active=True
        ).last()
        if user_personalise_obj:
            return get_max_heart_rate_from_age(user_personalise_obj.date_of_birth)
        return None

    def _get_user_weight(self, activity_datetime):
        weight_filtered_data = self.user_personalise_data_list.filter(
            weight__isnull=False, weight__gt=0
        )

        user_personalise_obj = (
            weight_filtered_data.filter(
                created_at__date__lte=activity_datetime.date()
            ).last()
            or weight_filtered_data.first()
        )
        return user_personalise_obj.weight if user_personalise_obj else None

    def _get_user_gender(self, activity_datetime):
        gender_filtered_data = UserProfile.objects.filter(
            gender__isnull=False, user_id=self.user_id
        )

        user_profile_obj = (
            gender_filtered_data.filter(
                created_at__date__lte=activity_datetime.date()
            ).last()
            or gender_filtered_data.first()
        )
        return user_profile_obj.gender if user_profile_obj else None

    def _get_user_age(self, activity_datetime):
        user_personalise_obj = self.user_personalise_data_list.filter(
            is_active=True
        ).last()
        return (
            user_personalise_obj.get_age(current_date=activity_datetime)
            if user_personalise_obj
            else None
        )

    def get_basic_info(self):
        user_info_from_daroan = daroan_get_athlete_info(self.user_id)
        user_profile = self._get_user_profile_data()
        user_personalise_data = self._get_user_personalise_data()
        return {
            "email": None
            if user_info_from_daroan["error"]
            else user_info_from_daroan["data"]["email"],
            "joining_date": None
            if user_info_from_daroan["error"]
            else user_info_from_daroan["data"]["joining_date"],
            "first_name": user_profile.name,
            "surname": user_profile.surname,
            "gender": GenderEnum.get_name(user_profile.gender)
            if user_profile.gender
            else None,
            "dob": user_personalise_data.date_of_birth,  # Deprecated from R17.2
            "age": user_personalise_data.get_age(),
            "weight": user_personalise_data.weight,
            "timezone": timezone_dict(user_profile),
        }

    def get_fitness_data(self, activity_datetime_str):
        activity_datetime = convert_str_date_time_to_date_time_obj(
            activity_datetime_str
        )
        self.user_personalise_data_list = self._get_user_personalise_data_list()
        return {
            "ftp": self._get_user_ftp(activity_datetime),
            "fthr": self._get_user_fthr(activity_datetime),
            "mhr": self._get_user_max_heart_rate(activity_datetime),
        }

    def get_fitness_data_in_daterange(self, start_date, end_date):
        self.user_personalise_data_list = self._get_user_personalise_data_list()
        for day in daterange(start_date, end_date):
            date_time = datetime.combine(day, datetime.min.time())
            return {
                "date": day,
                "ftp": self._get_user_ftp(date_time),
                "fthr": self._get_user_fthr(date_time),
                "mhr": self._get_user_max_heart_rate(date_time),
            }

    def get_current_fitness_data(self, calculate_mhr_from_age=True):
        user_personalise_data = self._get_user_personalise_data()
        """This is special condition, In some cases we might need to serve age calculated mhr data
        if mhr is None, and in some cases we have to serve None data"""
        if not user_personalise_data.max_heart_rate and calculate_mhr_from_age:
            mhr = get_max_heart_rate_from_age(user_personalise_data.date_of_birth)
        else:
            mhr = user_personalise_data.max_heart_rate

        return (
            {
                "ftp": user_personalise_data.current_ftp
                if user_personalise_data.current_ftp
                else None,
                "fthr": user_personalise_data.current_fthr
                if user_personalise_data.current_fthr
                else None,
                "mhr": mhr,
                "ftp_input_denied": user_personalise_data.ftp_input_denied,
                "fthr_input_denied": user_personalise_data.fthr_input_denied,
            }
            if user_personalise_data
            else {
                "ftp": None,
                "fthr": None,
                "mhr": None,
                "ftp_input_denied": None,
                "fthr_input_denied": None,
            }
        )

    def baseline_fitness_exist(self, activity_datetime_str):
        activity_datetime = convert_str_date_time_to_date_time_obj(
            activity_datetime_str
        )
        self.user_personalise_data_list = self._get_user_personalise_data_list()

        return {
            "ftp_exist": True if self._get_user_ftp(activity_datetime) else False,
            "fthr_exist": True if self._get_user_fthr(activity_datetime) else False,
            "mhr_exist": True
            if self._get_user_max_heart_rate(activity_datetime)
            else False,
        }

    def get_file_process_info(self, activity_datetime_str):
        activity_datetime = convert_str_date_time_to_date_time_obj(
            activity_datetime_str
        )
        self.user_personalise_data_list = self._get_user_personalise_data_list()
        user_profile = self._get_user_profile_data()
        return {
            "ftp": self._get_user_ftp(activity_datetime),
            "fthr": self._get_user_fthr(activity_datetime),
            "mhr": self._get_user_max_heart_rate(activity_datetime),
            "weight": self._get_user_weight(activity_datetime),
            "gender": self._get_user_gender(activity_datetime),
            "age": self._get_user_age(activity_datetime),
            "timezone_offset": user_profile.timezone.offset,
        }

    def save_fitness_info(self, **kwargs):
        user_personalise_data = self._get_user_personalise_data()
        user_personalise_data = create_new_model_instance(user_personalise_data)
        user_personalise_data.current_ftp = (
            kwargs["ftp"] if kwargs["ftp"] else user_personalise_data.current_ftp
        )
        user_personalise_data.current_fthr = (
            kwargs["fthr"] if kwargs["fthr"] else user_personalise_data.current_fthr
        )
        user_personalise_data.max_heart_rate = (
            kwargs["mhr"] if kwargs["mhr"] else user_personalise_data.max_heart_rate
        )

        logger.info("Saving user fitness info")
        user_personalise_data.save()

    @staticmethod
    def get_timezone_data():
        return CommonClass.get_time_zone_list_dict(
            TimeZone.objects.filter(is_active=True)
        )

    @classmethod
    @transaction.atomic
    def save_user_onboarding_data(cls, user_id, onboarding_input):
        """
        These two functions are called here together in atomic transaction so that
        profile data doesn't get saved without personalize data if some error occurs,
        which can cause conflict when user tries to onboard and save all the onboarding
        data again. In this way even if personalize data isn't saved due to an error,
        it won't be an issue as profile data too won't be saved.
        """
        response = UserProfileServiceV2.check_validity_of_threshold_values(
            onboarding_input.get("ftp"),
            onboarding_input.get("fthr"),
            onboarding_input.get("max_heart_rate"),
        )
        if response:
            # Above function will return response only if the threshold values are invalid
            return response
        logger.info("saving user profile data")
        user_profile = cls.save_user_profile_data(user_id, onboarding_input)
        logger.info("saving user personalise data")
        user_personalise_data = cls.save_user_personalise_data(
            user_id, onboarding_input
        )
        # cls.save_zone_difficulty_level(user_id, user_personalise_data)

        if settings.HUBSPOT_ENABLE:
            HubspotServiceV2(
                user_id=user_id,
                name=onboarding_input.get("name"),
                email=onboarding_input.get("email"),
            ).send_data()

        # TODO Refactor
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            user_profile.timezone.offset, datetime.now()
        )
        payload = {
            "is_onboarding_day": True,  # this api is invoked during onboarding so this field will be true
            "user_id": str(user_id),
            "calculation_date": str(user_local_date),
            "starting_actual_load": float(user_personalise_data.starting_load),
            "starting_actual_acute_load": float(
                user_personalise_data.starting_acute_load
            ),
            "full_name": user_profile.full_name,
        }
        calculate_morning_data(payload, user_id)

        logger.info(f"Saved user onboarding data successfully for user ID: {user_id}")
        return make_context(False, "Saved user onboarding data successfully", None)

    @classmethod
    @transaction.atomic
    def save_user_portal_onboarding_data(cls, user_id, onboarding_input):
        """
        These two functions are called here together in atomic transaction so that
        profile data doesn't get saved without personalize data if some error occurs,
        which can cause conflict when user tries to onboard and save all the onboarding
        data again. In this way even if personalize data isn't saved due to an error,
        it won't be an issue as profile data too won't be saved.
        """
        response = UserProfileServiceV2.check_validity_of_threshold_values(
            onboarding_input.get("ftp"),
            onboarding_input.get("fthr"),
            onboarding_input.get("max_heart_rate"),
        )
        if response:
            # Above function will return response only if the threshold values are invalid
            return response
        logger.info("saving user profile data")
        cls.save_user_profile_data(user_id, onboarding_input)
        logger.info("saving user personalise data")
        user_personalise_data = cls.save_user_personalise_data(
            user_id, onboarding_input
        )
        # cls.save_zone_difficulty_level(user_id, user_personalise_data)

        payload = {
            "is_onboarding_day": True,  # this api is invoked during onboarding so this field will be true
            "user_id": user_id,
            "calculation_date": str(date.today()),
            "starting_actual_load": float(user_personalise_data.starting_load),
            "starting_actual_acute_load": float(
                user_personalise_data.starting_acute_load
            ),
        }

        logger.info(f"Saved user onboarding data successfully for user ID: {user_id}")
        return make_context(
            False, "Saved user onboarding data successfully", data=payload
        )

    @staticmethod
    def check_validity_of_threshold_values(ftp, fthr, max_heart_rate):
        """Checks if the given threshold values by the user falls between the valid boundary values for those"""
        if ftp and not (FTP_BOUNDARY["lowest"] <= ftp <= FTP_BOUNDARY["highest"]):
            return make_context(
                True, "Please enter a viable FTP value. Accepted range is 30-500.", None
            )
        if fthr and not (FTHR_BOUNDARY["lowest"] <= fthr <= FTHR_BOUNDARY["highest"]):
            return make_context(
                True,
                "Please enter a viable FTHR value. Accepted range is 80-200.",
                None,
            )
        if max_heart_rate and not (
            MAX_HR_BOUNDARY["lowest"] <= max_heart_rate <= MAX_HR_BOUNDARY["highest"]
        ):
            return make_context(
                True,
                "Please enter a viable Max Heart Rate value. Accepted range is 100-230.",
                None,
            )

    @classmethod
    def save_user_profile_data(cls, user_id, onboarding_input):
        name = onboarding_input.get("name")
        gender = onboarding_input.get("gender")
        timezone_offset = onboarding_input.get("timezone_offset")

        name, surname = cls.get_user_name_and_surname(name)
        gender = UserProfileServiceV2.get_gender(gender) if gender else None

        timezone_offset = format_timezone(timezone_offset)
        if not timezone_offset:
            timezone_offset = UTC_TIMEZONE
        timezone = TimeZone.objects.get_closest_timezone(timezone_offset)

        user_profile = UserProfile.objects.filter(
            user_id=user_id, is_active=True
        ).last()
        if user_profile:
            logger.info("existing user profile object found. Creating new instance")
            user_profile.name = name
            user_profile.surname = surname
            user_profile = create_new_model_instance(user_profile)
            user_profile.save()
            return user_profile

        logger.info("No existing user profile object found. Creating new instance")
        user_profile = UserProfile.objects.create(
            name=name,
            surname=surname,
            timezone=timezone,
            user_id=user_id,
            gender=gender,
            unit_system=UserUnitSystemEnum.METRIC.value[0],
            access_level=UserAccessLevelEnum.HOME.value[0],
        )
        logger.info("Created user profile")

        return user_profile

    @staticmethod
    def save_user_personalise_data(user_id, onboarding_input):
        date_of_birth = onboarding_input.get("date_of_birth")  # Deprecated from R17.2
        age = onboarding_input.get("age")
        weight = onboarding_input.get("weight")
        ftp = onboarding_input.get("ftp")
        fthr = onboarding_input.get("fthr")
        max_heart_rate = onboarding_input.get("max_heart_rate")
        training_hours_over_last_4_weeks = onboarding_input.get("training_history")

        if age:
            date_of_birth = date.today() - relativedelta(years=age)
        else:
            date_of_birth = convert_str_date_to_date_obj(date_of_birth)

        ftp = round(ftp) if ftp else 0
        fthr = round(fthr) if fthr else 0
        starting_load = MIN_STARTING_LOAD
        starting_acute_load = MIN_STARTING_LOAD
        if training_hours_over_last_4_weeks:
            starting_load = get_user_starting_load_v2(training_hours_over_last_4_weeks)
            starting_acute_load = starting_load
            training_hours_over_last_4_weeks = [training_hours_over_last_4_weeks] * 4

        user_personalise_data = UserPersonaliseData.objects.filter(
            user_id=user_id, is_active=True
        ).last()
        if user_personalise_data:
            if date_of_birth:
                user_personalise_data.date_of_birth = date_of_birth
            if weight:
                user_personalise_data.weight = weight
            if ftp:
                user_personalise_data.current_ftp = ftp
            if fthr:
                user_personalise_data.current_fthr = fthr
            if max_heart_rate:
                user_personalise_data.max_heart_rate = max_heart_rate
            if training_hours_over_last_4_weeks:
                user_personalise_data.starting_load = starting_load
                user_personalise_data.starting_acute_load = starting_load
                user_personalise_data.training_hours_over_last_4_weeks = (
                    training_hours_over_last_4_weeks
                )
            user_personalise_data = create_new_model_instance(user_personalise_data)
            user_personalise_data.save()
            return user_personalise_data

        request_data = {
            "date_of_birth": date_of_birth,
            "weight": weight,
            "training_hours_over_last_4_weeks": training_hours_over_last_4_weeks or "",
            "starting_load": starting_load,
            "starting_acute_load": starting_acute_load,
            "current_ftp": ftp,
            "current_fthr": fthr,
            "max_heart_rate": max_heart_rate,
            "user_id": user_id,
        }

        return UserPersonaliseData.objects.create(**request_data)

    @staticmethod
    def get_gender(gender_input):
        """:param gender_input: user provided gender input"""
        if gender_input:
            for x in GenderEnum:
                if x.value[1].lower() == gender_input.lower():
                    return x.value[0]

    @staticmethod
    def get_user_name_and_surname(name_input):
        """:param name_input: user provided full name input"""
        return split_user_name(name_input)

    @classmethod
    def save_zone_difficulty_level(cls, user_id, user_personalise_data):
        if (
            user_personalise_data.starting_load
            and not ZoneDifficultyLevel.objects.filter(
                user_id=user_id, is_active=True
            ).exists()
        ):
            zone_difficulty_level = ZoneDifficultyLevel(
                user_id=user_id,
            )
            zone_difficulty_level.set_starting_zone_levels(
                user_personalise_data.starting_load
            )
            zone_difficulty_level.save()

    def _set_user_timezone(self, user_profile: UserProfile, timezone_id):
        logger.info("Set user timezone in profile")

        if timezone_id is None:
            logger.info("No timezone id found")
            return user_profile

        try:
            timezone = TimeZone.objects.get(id=timezone_id)
        except Exception as e:
            logger.exception(
                "Invalid Timezone ID",
                extra=log_extra_fields(
                    user_id=self.user_id,
                    service_type=ServiceType.API.value,
                    exception_message=str(e),
                ),
            )
            raise ValueError("Invalid Timezone ID")

        user_profile.timezone = timezone
        self.is_profile_data_fields_updated = True
        return user_profile

    def _set_user_weight(self, user_personalise_data: UserPersonaliseData, weight):
        logger.info("Set user weight in personalise table")
        if weight is None:
            logger.info("No weight data found")
            return user_personalise_data
        if not UserPersonaliseData.is_valid_weight(weight):
            raise ValidationError("Weight is not in acceptable range")

        user_personalise_data.weight = weight
        self.is_personalise_data_fields_updated = True

        return user_personalise_data

    def update_basic_info(self, **kwargs):
        user_profile = self._get_user_profile_data()

        user_profile = self._set_user_timezone(user_profile, kwargs["timezone_id"])

        if self.is_profile_data_fields_updated:
            user_profile = create_new_model_instance(user_profile)
            user_profile.save()

        user_personalise_data = self._get_user_personalise_data()
        user_personalise_data = self._set_user_weight(
            user_personalise_data, kwargs["weight"]
        )

        if self.is_personalise_data_fields_updated:
            user_personalise_data = create_new_model_instance(user_personalise_data)
            user_personalise_data.save()
        logger.info("Updated user basic info successfully")


class UserSupportServiceV2:
    @classmethod
    def post_user_support_message(cls, request):
        data = {
            "name": request.data.get("name"),
            "email": request.data.get("email"),
            "type_of_issue": request.data.get("type_of_issue"),
            "date_of_issue": request.data.get("date_of_issue"),
            "app_version": request.data.get("app_version"),
            "message": request.data.get("message"),
            "device_model": request.data.get("device_model"),
        }

        if request.data.get("file") is not None:
            data["attachment_url"] = cls._process_user_support_attachment(
                request.data["file"]
            )
        if request.data.get("user_log") is not None:
            data["user_log"] = cls._process_user_support_attachment(
                request.data["user_log"]
            )
        cls.notion_and_slack_action(data)

    @classmethod
    def _process_user_support_attachment(cls, file):
        local_file_path, file_name = cls._save_file_local(file)
        s3_file_url = cls._upload_file_s3(local_file_path, file_name)
        return s3_file_url

    @classmethod
    def _save_file_local(cls, file):
        # save file in local directory form request body
        current_path = os.path.dirname(__file__) + "/user_support_attachment/"
        fs = FileSystemStorage(current_path)
        filename = fs.save(file.name, file)
        uploaded_file_url = fs.url(filename)
        local_file_path = current_path + file.name

        return local_file_path, uploaded_file_url

    @classmethod
    def _upload_file_s3(cls, local_file_path, file_name):
        # Creating Session With Boto3.
        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        # generate file name with timestamp
        unique_text = "/" + str(time.time()) + "-"
        file_name = file_name.replace("/media/", unique_text)

        # Creating S3 Resource From the Session.
        s3 = session.resource("s3")
        bucket_name = "user-support-pillar"
        s3_file_path = "user_support_attachment" + file_name

        # upload file to s3
        s3.Bucket(bucket_name).upload_file(local_file_path, s3_file_path)
        logger.info("File uploaded successfully to S3")

        # remove file from local directory
        os.remove(local_file_path)
        logger.info("Remove File From Local Directory")

        # get file url
        uploaded_file_url = cls._generate_s3_uploaded_file_url(s3_file_path)
        return uploaded_file_url

    @classmethod
    def _generate_s3_uploaded_file_url(cls, s3_file_path):
        base_url = ""
        return base_url + s3_file_path

    @classmethod
    def _post_to_notion_board(cls, notion_payload):
        url = ""

        payload = json.dumps(notion_payload)
        headers = {
            "Authorization": "",
            "Content-Type": "application/json",
            "Notion-Version": "",
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info(response.json())
        notion_url = response.json().get("url")
        logger.info("Successfully posted to notion board")
        return notion_url

    @classmethod
    def _generate_notion_payload(cls, data):
        notion_payload = {
            "parent": {"database_id": ""},
            "properties": {
                "Support ID": {
                    "type": "title",
                    "title": [{"text": {"content": data.get("support_id")}}],
                },
                "Name": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": data.get("name")}}],
                },
                "Email": {"type": "email", "email": data.get("email")},
                "Type of Issue": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": data.get("type_of_issue")}}],
                },
                "Date of Issue": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": data.get("date_of_issue")}}],
                },
                "App Version": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": data.get("app_version")}}],
                },
                "Message": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": data.get("message")}}],
                },
                "Device Model": {
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": data.get("device_model")}}],
                },
                "Attachment": {"url": data.get("attachment_url")},
                "User Log": {"url": data.get("user_log")},
            },
        }
        return notion_payload

    @classmethod
    def _post_to_slack_channel(cls, slack_payload):
        url = ""
        payload = json.dumps(slack_payload)
        headers = {"Content-type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info(response)
        logger.info("Successfully posted to slack channel")

    @classmethod
    def _generate_slack_payload(cls, data):
        slack_payload = {
            "text": data.get("message"),
            "blocks": [
                {
                    "type": "section",
                    "fields": [
                        
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{data.get('message')}"},
                },
                {"type": "divider"},
            ],
        }
        return slack_payload

    @classmethod
    def _generate_support_id(cls, data):
        app_version = data.get("app_version")
        current_time = int(time.time())
        support_id = f"{app_version}-{current_time}"
        return support_id

    @classmethod
    def notion_and_slack_action(cls, data):
        data["support_id"] = cls._generate_support_id(data)
        notion_payload = cls._generate_notion_payload(data)
        data["notion_url"] = cls._post_to_notion_board(notion_payload)
        slack_payload = cls._generate_slack_payload(data)
        cls._post_to_slack_channel(slack_payload)
        user_support_mail(data["email"], data["support_id"], data["name"])


class HubspotServiceV2:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.name = kwargs.get("name")
        self.email = kwargs.get("email")

        self.time = round(time.time() * 1000)
        self.url = self._get_url()
        self.headers = self._get_headers()
        self.payload = self._generate_payload()

    @staticmethod
    def _get_url():
        portal_id = ""
        form_guid = ""
        base_url = ""
        return f"{base_url}{portal_id}/{form_guid}"

    @staticmethod
    def _get_headers():
        return {
            "content-type": "application/json",
            "cache-control": "no-cache",
        }

    def _generate_payload(self):
        payload = {
            "submittedAt": self.time,
            "fields": [
                {"name": "email", "value": self.email},
                {"name": "firstname", "value": self.name},
            ],
            "context": {"pageName": "App Registration"},
            "legalConsentOptions": {
                "consent": {
                    "consentToProcess": True,
                    "text": "I agree to allow Pillar App Ltd. to store and process my personal data.",
                    "communications": [
                        {
                            "value": True,
                            "subscriptionTypeId": 999,
                            "text": "I agree to receive marketing communications from Pillar App Ltd.",
                        }
                    ],
                }
            },
        }

        # need to convert to string, otherwise it won't be accepted by hubspot
        return json.dumps(payload)

    def send_data(self):
        try:
            response = requests.post(self.url, data=self.payload, headers=self.headers)
            logger.info(
                response.text,
                extra=log_extra_fields(
                    user_id=self.user_id, service_type=ServiceType.API.value
                ),
            )
        except Exception as e:
            logger.exception(
                "Failed to send user data to hubspot",
                extra=log_extra_fields(
                    user_id=self.user_id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                ),
            )
