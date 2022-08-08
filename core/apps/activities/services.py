import json
import logging
import os
from datetime import date, timedelta
from pathlib import Path

import requests
import xlsxwriter
from django.conf import settings
from smart_open import smart_open

from core.apps.activities.tasks import recalculate_data_for_daterange
from core.apps.common.const import PILLAR_DATA_FILE_EXTENSION
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.utils import (
    dakghor_connect_athlete,
    get_activity_file_name,
    upload_file_to_s3,
)
from core.apps.garmin.models import CurveCalculationData
from core.apps.plan.models import UserPlan
from core.apps.session.models import ActualSession
from core.apps.user_profile.services import get_user_local_date

from .enums import SecondBySecondDataEnum

logger = logging.getLogger(__name__)


class ReevaluationService:
    @classmethod
    def reevaluate_session_data_of_single_plan(
        cls, user_auth, user_plan: UserPlan, start_date: date
    ):
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = min(get_user_local_date(user_auth), user_plan.end_date).strftime(
            "%Y-%m-%d"
        )
        recalculate_data_for_daterange.delay(user_auth.id, start_date, end_date)

    @classmethod
    def reevaluate_session_outside_plan(
        cls, user_auth, reevaluation_end_date, user_plans
    ):
        """Run reevaluation in between User Plans"""
        start_date = None
        for user_plan in user_plans:
            if start_date:
                end_date = user_plan.start_date - timedelta(days=1)
                if (end_date - start_date).days > 0:
                    recalculate_data_for_daterange.delay(
                        user_auth.id,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                    )
            start_date = user_plan.end_date + timedelta(days=1)

        if start_date:
            end_date = reevaluation_end_date
            if (end_date - start_date).days > 0:
                recalculate_data_for_daterange.delay(
                    user_auth.id,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )

    @classmethod
    def reevaluate_session_data(cls, user_auth, start_date: date, end_date: date):
        user_plans = UserPlan.objects.filter(
            user_auth=user_auth,
            is_active=True,
            end_date__gte=start_date,
            start_date__lte=end_date,
        ).order_by("end_date")

        for user_plan in user_plans:
            cls.reevaluate_session_data_of_single_plan(
                user_auth, user_plan, max(start_date, user_plan.start_date)
            )

        cls.reevaluate_session_outside_plan(user_auth, end_date, user_plans)

    @classmethod
    def reevaluate_session_data_from_fitfile(
        cls, user_auth, start_date: date, end_date: date
    ):
        # TODO: Complete in R9 S1
        pass

    @classmethod
    def reevaluate_complete_user_data(
        cls, user_auth, start_date, end_date, is_recalculating_fitfile=False
    ):
        end_date = min(end_date, get_user_local_date(user_auth))
        if is_recalculating_fitfile:
            cls.reevaluate_session_data_from_fitfile(user_auth, start_date, end_date)
        else:
            cls.reevaluate_session_data(user_auth, start_date, end_date)


class DakghorDataTransferService:
    strava_files_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "activityfiles"
    )

    @staticmethod
    def write_data_to_excel(worksheet, ride_data, user_auth, activity_datetime):
        power_data = ride_data.second_by_second_power
        power_data = eval(power_data) if power_data else []
        i = 1
        for power in power_data:
            worksheet.write(i, SecondBySecondDataEnum.POWER.value[0], power["value"])
            worksheet.write(
                i, SecondBySecondDataEnum.POWER_ZONE.value[0], power["zone_focus"]
            )
            i += 1

        hr_data = ride_data.second_by_second_hr
        hr_data = eval(hr_data) if hr_data else []
        i = 1
        for hr in hr_data:
            worksheet.write(i, SecondBySecondDataEnum.HEART_RATE.value[0], hr["value"])
            worksheet.write(
                i, SecondBySecondDataEnum.HEART_RATE_ZONE.value[0], hr["zone_focus"]
            )
            i += 1

        column_data = [
            (SecondBySecondDataEnum.SPEED, ride_data.second_by_second_speed),
            (SecondBySecondDataEnum.CADENCE, ride_data.second_by_second_cadence),
            (SecondBySecondDataEnum.DISTANCE, ride_data.second_by_second_distance),
            (SecondBySecondDataEnum.ELEVATION, ride_data.second_by_second_elevation),
            (
                SecondBySecondDataEnum.TEMPERATURE,
                ride_data.second_by_second_temperature,
            ),
            (SecondBySecondDataEnum.TIME, ride_data.second_by_second_time),
            (SecondBySecondDataEnum.LATITUDE, ride_data.second_by_second_latitude),
            (SecondBySecondDataEnum.LONGITUDE, ride_data.second_by_second_longitude),
            (
                SecondBySecondDataEnum.LEFT_LEG_POWER,
                ride_data.second_by_second_left_leg_power
                if hasattr(ride_data, "second_by_second_left_leg_power")
                else "",
            ),
            (
                SecondBySecondDataEnum.RIGHT_LEG_POWER,
                ride_data.second_by_second_right_leg_power
                if hasattr(ride_data, "second_by_second_right_leg_power")
                else "",
            ),
        ]

        for column_num, value in column_data:
            value = json.loads(value) if value else []
            if column_num == SecondBySecondDataEnum.TIME:
                worksheet.write_column(1, column_num.value[0], value)
            else:
                value = [data["value"] for data in value]
                worksheet.write_column(1, column_num.value[0], value)

        return worksheet

    @staticmethod
    def write_header(worksheet):
        for data in SecondBySecondDataEnum:
            worksheet.write(0, data.value[0], data.value[1])

        return worksheet

    @classmethod
    def store_data_in_xlsx_format(
        cls, file_path, ride_data, user_auth, activity_datetime
    ):
        with smart_open(file_path, "wb") as file:
            workbook = xlsxwriter.Workbook(file)
            worksheet = workbook.add_worksheet()

            worksheet = cls.write_header(worksheet=worksheet)
            cls.write_data_to_excel(worksheet, ride_data, user_auth, activity_datetime)
            workbook.close()

    @staticmethod
    def create_activity_dict(
        user_auth, source, s3_pillar_file, ride_data, activity_datetime
    ):
        return {
            "id": ride_data.id,
            "source": source,
            "athlete_id": user_auth.id,
            "file_id": ride_data.activity_file_id
            if hasattr(ride_data, "activity_file_id")
            else ride_data.activity_id,
            "third_party_file": ride_data.file_name,
            "pillar_file": s3_pillar_file,
            "file_type": ride_data.file_type,
            "type": ride_data.activity_type,
            "sub_type": ride_data.activity_sub_type,
            "start_time": activity_datetime,
            "distance": ride_data.total_distance_in_meter,
            "manufacturer": ride_data.manufacturer
            if hasattr(ride_data, "manufacturer")
            else None,
            "elapsed_time": ride_data.elapsed_time_in_seconds,
            "moving_time": ride_data.moving_time_in_seconds,
            "moving_fraction": ride_data.moving_fraction,
            "elevation_gain": ride_data.elevation_gain,
            "weighted_power": ride_data.weighted_power,
            "ride_summary": ride_data.ride_summary,
            "time_in_heart_rate_zone": ride_data.actual_time_in_hr_zone,
            "time_in_power_zone": ride_data.actual_time_in_power_zone,
            "flagged_values": ride_data.flagged_values,
        }

    @classmethod
    def move_table_data_to_s3(
        cls,
        ride_data,
        activity_files_path,
        s3_pillar_file,
        user_auth,
        activity_datetime,
    ):
        Path(activity_files_path).mkdir(parents=True, exist_ok=True)

        activity_file_name = get_activity_file_name(
            ride_data.user_auth_id, file_extension=PILLAR_DATA_FILE_EXTENSION
        )
        local_file_path = os.path.join(activity_files_path, activity_file_name)
        cls.store_data_in_xlsx_format(
            local_file_path, ride_data, user_auth, activity_datetime
        )

        logger.info(f"Uploading file to S3, User: {user_auth.id}")
        upload_file_to_s3(local_file_path, s3_pillar_file)
        os.remove(local_file_path)

    @classmethod
    def send_activities(cls, user_auth, activities):
        url = settings.DAKGHOR_URL + "/api/v1/third-party/data-migrate"

        if activities:
            response = requests.post(url=url, json={"activities": activities})
            athlete_activities = response.json()["data"]["athlete_activities"]
            for athlete_activity in athlete_activities:
                if (
                    athlete_activity["source"]
                    == ThirdPartySources.GARMIN.value[1].lower()
                ):
                    actual_sessions = ActualSession.objects.filter(
                        user_auth=user_auth, garmin_data_id=athlete_activity["id"]
                    )
                else:
                    actual_sessions = ActualSession.objects.filter(
                        user_auth=user_auth, strava_data_id=athlete_activity["id"]
                    )
                actual_sessions.update(
                    athlete_activity_code=athlete_activity["athlete_activity_code"],
                    elevation_gain=athlete_activity["elevation_gain"],
                )
                CurveCalculationData.objects.filter(
                    ride_data_id=athlete_activity["id"],
                    source=ThirdPartySources.get_code_from_text(
                        athlete_activity["source"]
                    ),
                ).update(
                    athlete_activity_code=athlete_activity["athlete_activity_code"]
                )

    @classmethod
    def move_user_info_to_dakghor(cls, user_auth):
        if user_auth.garmin_user_id:
            dakghor_connect_athlete(
                athlete_id=user_auth.id,
                source=ThirdPartySources.GARMIN.value[1].lower(),
                user_id=user_auth.garmin_user_id,
                user_token=user_auth.garmin_user_token,
                user_secret=user_auth.garmin_user_secret,
            )

        if user_auth.strava_user_id:
            dakghor_connect_athlete(
                athlete_id=user_auth.id,
                source=ThirdPartySources.STRAVA.value[1].lower(),
                user_id=user_auth.strava_user_id,
                user_token=user_auth.strava_user_token,
                user_name=user_auth.strava_user_name,
                refresh_token=user_auth.strava_refresh_token,
                expires_at=user_auth.strava_token_expires_at,
            )
