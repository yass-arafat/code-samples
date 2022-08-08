import logging

from django_rq import job

from core.apps.garmin.models import CurveCalculationData

from .enums.third_party_sources_enum import ThirdPartySources
from .tp_common_utils import (
    calculate_curve,
    read_s3_pillar_heart_rate_data,
    read_s3_pillar_power_data,
)
from .utils import create_new_model_instance, log_extra_fields, read_s3_xlsx_file

logger = logging.getLogger(__name__)


# @shared_task
def calculate_power_curve_data(curve_data_id, s3_pillar_file_path):
    try:
        worksheet = read_s3_xlsx_file(s3_pillar_file_path)
        power_data = read_s3_pillar_power_data(worksheet)

        curve_power_data = calculate_curve(power_data)
        if curve_power_data is None:
            logger.info(f"No power curve found. {curve_power_data}")

        logger.info("Saving power curve data")
        curve_data = CurveCalculationData.objects.filter(pk=curve_data_id).first()
        curve_data.power_curve = str(curve_power_data)
        curve_data.save(update_fields=["power_curve", "updated_at"])
    except Exception as e:
        logger.exception(
            f"Failed to calculate power curve data. curve_data id: {curve_data_id}",
            extra=log_extra_fields(exception_message=str(e)),
        )


# @shared_task
def calculate_hr_curve_data(curve_data_id, s3_pillar_file_path):
    try:
        worksheet = read_s3_xlsx_file(s3_pillar_file_path)
        hr_data = read_s3_pillar_heart_rate_data(worksheet)

        curve_hr_data = calculate_curve(hr_data)
        if curve_hr_data is None:
            logger.info(f"No heart rate curve found. {curve_hr_data}")

        logger.info("Saving heart rate curve data")
        curve_data = CurveCalculationData.objects.filter(pk=curve_data_id).first()
        curve_data.heart_rate_curve = str(curve_hr_data)
        curve_data.save(update_fields=["heart_rate_curve", "updated_at"])
    except Exception as e:
        logger.exception(
            f"Failed to calculate heart rate curve data. curve_data id: {curve_data_id}",
            extra=log_extra_fields(exception_message=str(e)),
        )


# @shared_task
def calculate_curve_data(user_auth_id, user_auth_code, activity):
    source = ThirdPartySources.get_code_from_text(activity["source"])
    try:
        curve_data = CurveCalculationData.objects.get(
            athlete_activity_code=activity["code"], source=source, is_active=True
        )
        curve_data = create_new_model_instance(curve_data)
        logger.info("Curve data object creation done")
    except CurveCalculationData.DoesNotExist:
        curve_data = CurveCalculationData(
            user_auth_id=user_auth_id,
            user_id=user_auth_code,
            activity_datetime=activity["start_time"],
            activity_type=activity["type"],
            athlete_activity_code=activity["code"],
            source=source,
        )
    curve_data.save()
    logger.info("Saved curve data and starting to calculate power data")
    calculate_power_curve_data.delay(curve_data.id, activity["pillar_file"])
    logger.info("Saved curve data and starting to calculate heart rate data")
    calculate_hr_curve_data.delay(curve_data.id, activity["pillar_file"])


@job
def recalculate_user_all_curve_data(user_auth):
    pass
