import logging

from core.apps.achievements.dictionary import (
    get_personal_record_details,
    get_personal_record_history,
)
from core.apps.achievements.enums.record_types import RecordTypes
from core.apps.achievements.models import PersonalRecord
from core.apps.achievements.utils import RecordAttributes
from core.apps.common.common_functions import remove_exponent
from core.apps.common.const import PERSONAL_RECORD_DURATION_CHECK_UNIT
from core.apps.session.models import ActualSession

logger = logging.getLogger(__name__)


class AchievementService:
    @staticmethod
    def get_achievement_overview(user):
        """Returns the list of achieved personal record badges"""
        achievements = []
        for record_type in RecordTypes.ids():
            personal_record = PersonalRecord.objects.filter(
                user_auth=user, is_active=True, record_type=record_type
            ).last()
            is_active = True if personal_record else False
            badge_url = RecordAttributes.get_record_badge_url(record_type, is_active)
            achievements.append(badge_url)

        return {"achievements": achievements}

    @staticmethod
    def get_personal_records(user):
        """Returns details and history of a specific personal record"""
        personal_records = []
        date_time = None

        for record_type in RecordTypes.ids():
            personal_record = PersonalRecord.objects.filter(
                user_auth=user, is_active=True, record_type=record_type
            ).last()
            is_active = True if personal_record else False
            badge_url = RecordAttributes.get_record_badge_url(record_type, is_active)[
                "badge"
            ]
            record_type_name = RecordAttributes.get_record_type_name(record_type)

            if personal_record:
                actual_session = ActualSession.objects.filter(
                    is_active=True, code=personal_record.actual_session_code
                ).last()
                date_time = actual_session.session_date_time

            level = personal_record.record_level.level if personal_record else None

            value = (
                remove_exponent(personal_record.record_level.required_value)
                if personal_record
                else None
            )
            unit = personal_record.record_level.unit if personal_record else None
            if unit == PERSONAL_RECORD_DURATION_CHECK_UNIT and value >= 60:
                hour = int(value / 60)
                minutes = value - (hour * 60)
                value = f"{hour} h {minutes} m"
            elif value:
                value = f"{value}"
                if unit:
                    value += f" {unit}"

            metadata = {"is_active": is_active, "record_type": record_type}

            record = get_personal_record_details(
                badge_url, record_type_name, date_time, value, level, metadata=metadata
            )
            personal_records.append(record)

        return {"personal_records": personal_records}

    @staticmethod
    def get_record_detail(user, record_type):
        """Returns details and history of a specific personal record"""

        personal_records = PersonalRecord.objects.filter(
            user_auth=user, is_active=True, record_type=record_type
        )
        current_record = personal_records.last()

        badge_url = RecordAttributes.get_record_badge_url(record_type)["badge"]
        record_type_name = RecordAttributes.get_record_type_name(record_type)
        actual_session = ActualSession.objects.filter(
            is_active=True, code=current_record.actual_session_code
        ).last()
        level = current_record.record_level.level

        value = remove_exponent(current_record.record_level.required_value)
        unit = current_record.record_level.unit
        if unit == PERSONAL_RECORD_DURATION_CHECK_UNIT and value >= 60:
            hour = int(value / 60)
            minutes = value - (hour * 60)
            value = f"{hour} h {minutes} m"
        elif value:
            value = f"{value}"
            if unit:
                value += f" {unit}"

        history = get_personal_record_history(list(personal_records)[:-1], user)

        return get_personal_record_details(
            badge_url,
            record_type_name,
            actual_session.session_date_time,
            value,
            level,
            history,
        )
