import logging
from datetime import timedelta

from core.apps.achievements.enums.record_types import RecordTypes
from core.apps.achievements.models import PersonalRecord, RecordLevel, RecordType
from core.apps.achievements.record_badge_urls import (
    RECORD_BADGE_URLS,
    RECORD_GREY_BADGE_URLS,
)
from core.apps.activities.pillar.utils import get_average_speed_from_ride_summary
from core.apps.activities.utils import dakghor_get_athlete_activity
from core.apps.common.common_functions import clear_user_cache
from core.apps.common.const import TIME_RANGE_BOUNDARY
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import log_extra_fields, update_is_active_value
from core.apps.session.models import ActualSession

logger = logging.getLogger(__name__)


def check_personal_records(user, actual_session, average_speed):
    """Checks if user has achieved any personal record in actual session's activity"""
    # TODO: Need to remove the priority check part and refactor, as priority check can be done outside the function
    extra_log_fields = log_extra_fields(
        user_auth_id=user.id, service_type=ServiceType.INTERNAL.value
    )
    logger.info("Personal record check starts", extra=extra_log_fields)

    start_time = actual_session.session_date_time - timedelta(
        seconds=TIME_RANGE_BOUNDARY
    )
    end_time = actual_session.session_date_time + timedelta(seconds=TIME_RANGE_BOUNDARY)
    actual_sessions = ActualSession.objects.filter(
        user_auth=actual_session.user_auth,
        session_date_time__range=(start_time, end_time),
        is_active=True,
    ).exclude(id=actual_session.id)
    if actual_session.session_code:
        session = (
            actual_sessions.filter(session_code=actual_session.session_code)
            .order_by("third_party__priority")
            .first()
        )
    else:
        session = (
            actual_sessions.filter(session_code__isnull=True)
            .order_by("third_party__priority")
            .first()
        )

    if (
        session is None
        or actual_session.third_party.priority < session.third_party.priority
    ):
        # Deactivate the achievements from lower priority activity
        elevation_gain = actual_session.elevation_gain
        duration = actual_session.actual_duration
        distance = actual_session.actual_distance_in_meters / 1000  # Convert in km

        if session:
            personal_records = PersonalRecord.objects.filter(
                actual_session_code=session.code, is_active=True
            )
            update_is_active_value(personal_records, False)

        achieved_value_list = [elevation_gain, duration, distance, average_speed]

        for record_id, achieved_value in zip(RecordTypes.ids(), achieved_value_list):
            create_achieved_personal_record_entry(
                record_id, achieved_value, actual_session.code, user
            )

    clear_user_cache(user)
    logger.info("Personal record check ends", extra=extra_log_fields)


class RecordAttributes:
    biggest_elevation_record_id = RecordTypes.BIGGEST_ELEVATION.value[0]
    longest_ride_record_id = RecordTypes.LONGEST_RIDE.value[0]
    furthest_ride_record_id = RecordTypes.FURTHEST_RIDE.value[0]
    fastest_ride_record_id = RecordTypes.FASTEST_RIDE.value[0]

    @staticmethod
    def get_record_badge_url(record_type, is_active=True):
        """Returns badge url of the corresponding record type. is_active is true if the record_type is unlocked"""
        if is_active:
            return {"badge": RECORD_BADGE_URLS[record_type]}
        return {"badge": RECORD_GREY_BADGE_URLS[record_type]}

    @classmethod
    def get_record_type_name(cls, record_type):
        """Returns the name of the record type in a string format"""
        record_type_name = None
        if record_type == cls.biggest_elevation_record_id:
            record_type_name = RecordTypes.BIGGEST_ELEVATION.value[1]
        elif record_type == cls.longest_ride_record_id:
            record_type_name = RecordTypes.LONGEST_RIDE.value[1]
        elif record_type == cls.furthest_ride_record_id:
            record_type_name = RecordTypes.FURTHEST_RIDE.value[1]
        elif record_type == cls.fastest_ride_record_id:
            record_type_name = RecordTypes.FASTEST_RIDE.value[1]

        return record_type_name


def create_achieved_personal_record_entry(
    record_id, achieved_value, actual_session_code, user
):
    """
    Checks what levels were achieved in current session. If those levels are new, makes entry to the personal record
    table as this means the user just achieved this level of the record type which is indicated by the record_id.
    """
    try:
        achieved_levels = RecordLevel.objects.filter(
            is_active=True, record_type=record_id, required_value__lte=achieved_value
        )
    except ValueError:
        return None
    for achieved_level in achieved_levels:
        if not PersonalRecord.objects.filter(
            user_auth=user,
            record_level=achieved_level,
            record_type=record_id,
            is_active=True,
        ).exists():
            PersonalRecord(
                user_auth=user,
                user_id=user.code,
                record_level=achieved_level,
                record_type=RecordType.objects.get(pk=record_id),
                actual_session_code=actual_session_code,
            ).save()
            logger.info(
                f"Personal Record saved, record type id: {record_id}, achieved level: {achieved_level.level}"
            )


def update_user_achievement_data(user, start_date, end_date):
    """Updates user achievement related data (e.g. Personal record, challenge/trophy) from start date to end date"""
    logger.info(f"Update achievement data for user: {user.id} starts.")
    actual_sessions = ActualSession.objects.filter_actual_sessions(
        user_auth=user,
        activity_type=ActivityTypeEnum.CYCLING.value[1],
        session_date_time__date__range=(start_date, end_date),
    )

    for actual_session in actual_sessions:
        if actual_session.athlete_activity_code:
            athlete_activity = dakghor_get_athlete_activity(
                actual_session.athlete_activity_code
            ).json()["data"]["athlete_activity"]
            average_speed = get_average_speed_from_ride_summary(
                athlete_activity["ride_summary"]
            )
        else:
            manual_activity_data = actual_session.pillar_data
            average_speed = (
                manual_activity_data.average_speed if manual_activity_data else 0
            )

        check_personal_records(user, actual_session, average_speed)

    logger.info(f"Update achievement data for user: {user.id} ends.")
