from core.apps.common.common_functions import remove_exponent
from core.apps.common.const import PERSONAL_RECORD_DURATION_CHECK_UNIT
from core.apps.session.models import ActualSession


def get_personal_record_history(personal_records, user):
    """Returns the history of a particular record type"""
    history = []
    actual_sessions = ActualSession.objects.filter(
        is_active=True,
        user_auth=user,
        code__in=[record.actual_session_code for record in personal_records],
    )
    for personal_record in personal_records:
        required_value = remove_exponent(personal_record.record_level.required_value)
        actual_session = actual_sessions.filter(
            code=personal_record.actual_session_code
        ).last()
        unit = personal_record.record_level.unit
        value = ""
        if unit == PERSONAL_RECORD_DURATION_CHECK_UNIT and required_value >= 60:
            hour = int(required_value / 60)
            minutes = required_value - (hour * 60)
            if hour:
                value = "1 hour" if hour < 2 else f"{hour} hours"
                value += f" {minutes} minutes" if minutes else ""
            elif minutes:
                value = f"{minutes} minutes"
        elif required_value:
            value = f"{required_value}"
            if unit:
                value += f" {unit}"
        history_dict = {
            "level": personal_record.record_level.level,
            "value": value,
            "date_time": actual_session.session_date_time,
        }
        history.append(history_dict)

    return history


def get_personal_record_details(
    badge_url, record_type_name, date_time, value, level, history=None, metadata=None
):
    return {
        "badge": badge_url,
        "name": record_type_name,
        "date_time": date_time,
        "value": value,
        "level": level,
        "history": history,
        "achievement_metadata": metadata,
    }
