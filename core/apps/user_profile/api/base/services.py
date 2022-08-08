import logging

from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    create_new_model_instance,
    get_max_heart_rate_from_age,
    log_extra_fields,
)
from core.apps.user_profile.models import UserPersonaliseData
from core.apps.user_profile.services import get_user_starting_load_v2

logger = logging.getLogger(__name__)


class PersonaliseDataService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_personalise_data = None
        self.user_personalise_data_list = None

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

    def _get_user_age(self, activity_datetime):
        user_personalise_obj = self.user_personalise_data_list.filter(
            is_active=True
        ).last()
        return (
            user_personalise_obj.get_age(current_date=activity_datetime)
            if user_personalise_obj
            else None
        )

    def save_current_personalise_data(self, **kwargs):
        logger.info("Saving user personalise data")

        self.user_personalise_data = self._get_user_personalise_data()

        user_personalise_data = create_new_model_instance(self.user_personalise_data)

        if kwargs["training_hours_over_last_4_weeks"] is not None:
            starting_load = get_user_starting_load_v2(
                kwargs["training_hours_over_last_4_weeks"]
            )
            user_personalise_data.starting_load = starting_load
            user_personalise_data.starting_acute_load = starting_load
            user_personalise_data.training_hours_over_last_4_weeks = [
                kwargs["training_hours_over_last_4_weeks"]
            ] * 4

        if kwargs["ftp"] is not None:
            user_personalise_data.current_ftp = kwargs["ftp"]
        if kwargs["threshold_heart_rate"] is not None:
            user_personalise_data.current_fthr = kwargs["threshold_heart_rate"]
        if kwargs["max_heart_rate"] is not None:
            user_personalise_data.max_heart_rate = kwargs["max_heart_rate"]

        user_personalise_data.save()

        logger.info("User personalise data saved successfully")

    def get_personalise_data(self, activity_datetime):
        self.user_personalise_data_list = self._get_user_personalise_data_list()
        return {
            "ftp": self._get_user_ftp(activity_datetime),
            "fthr": self._get_user_fthr(activity_datetime),
            "mhr": self._get_user_max_heart_rate(activity_datetime),
            "weight": self._get_user_weight(activity_datetime),
            "age": self._get_user_age(activity_datetime),
        }

    def get_current_personalise_data(self):
        self.user_personalise_data = self._get_user_personalise_data()

        return {
            "ftp": self.user_personalise_data.current_ftp,
            "fthr": self.user_personalise_data.current_fthr,
            "mhr": self.user_personalise_data.max_heart_rate,
            "weight": self.user_personalise_data.weight,
            "age": self.user_personalise_data.get_age(),
        }

    def get_personalise_data_list(self):
        """Returns all active personalise data of user"""
        return list(
            UserPersonaliseData.objects.filter(user_id=self.user_id)
            .all()
            .values("created_at", "updated_at", "weight")
        )
