import logging
from datetime import timedelta

from core.apps.common.date_time_utils import (
    convert_str_date_time_to_date_time_obj,
    daterange,
)
from core.apps.common.enums.response_code import ResponseCode

from .enums.event_sub_type_enum import ClimbingRatioEnum, EventSubTypeEnum
from .enums.event_type_enum import EventTypeEnum
from .enums.performance_goal_enum import PerformanceGoalEnum
from .models import EventType, NamedEvent, UserEvent

logger = logging.getLogger(__name__)


class UserEventService:
    @staticmethod
    def set_user_event_data(request, user):
        event_data = request.data.get("event_data")
        user_event = UserEvent()

        user_event_name = event_data.get("event_name") or ""
        user_event.name = user_event_name[:55]
        distance_per_day = event_data.get("distance_per_day") or 0.0
        elevation_gain = event_data.get("elevation_gain") or 0.0

        performance_goal = event_data.get("performance_goal")

        event_duration_in_days = event_data.get("event_duration_in_days") or 1
        event_start_date = convert_str_date_time_to_date_time_obj(
            event_data.get("event_date")
        ).date()
        event_end_date = event_start_date + timedelta(days=event_duration_in_days - 1)
        user_event.start_date = event_start_date
        user_event.end_date = event_end_date

        named_event_id = event_data.get("id")
        named_event = (
            NamedEvent.objects.filter(id=named_event_id)
            .select_related("event_type")
            .first()
        )
        if named_event_id and not named_event:
            return None, "No named event found with the event id"

        event_sub_type = event_data.get("event_sub_type")
        if not event_sub_type:
            if distance_per_day <= 0:
                return None, "Distance must be grater than 0"
            climbing_ratio = elevation_gain / distance_per_day
            if (
                ClimbingRatioEnum.FLAT.value[0]
                <= climbing_ratio
                <= ClimbingRatioEnum.FLAT.value[1]
            ):
                event_sub_type = EventSubTypeEnum.FLAT.value[1]
            elif (
                ClimbingRatioEnum.HILLY.value[0]
                < climbing_ratio
                <= ClimbingRatioEnum.HILLY.value[1]
            ):
                event_sub_type = EventSubTypeEnum.HILLY.value[1]
            else:
                event_sub_type = EventSubTypeEnum.MOUNTAIN.value[1]
        event_sub_type_value = EventSubTypeEnum.get_value_from_name(event_sub_type)

        if named_event:
            event_type = named_event.event_type
        else:
            event_type_name = event_data.get("event_type")
            event_type_value = EventTypeEnum.get_code_from_serialized_name(
                event_type_name
            )
            event_type = EventType.objects.filter(
                type=event_type_value, sub_type=event_sub_type_value
            ).first()

        if not event_type:
            return None, "Event type not found for given event details"

        user_event.event_type = event_type
        user_event.named_event_id = named_event_id
        user_event.distance_per_day = distance_per_day
        user_event.elevation_gain = elevation_gain

        for x in PerformanceGoalEnum:
            if x.value[1] == performance_goal:
                user_event.performance_goal = x.value[0]
                break
        user_event.user_auth = user
        user_event.user_id = user.code

        return user_event

    @classmethod
    def save_user_event_data(cls, request, user):
        user_event = cls.set_user_event_data(request, user)
        user_event.save()
        return user_event, "saved user event successfullly"


def get_named_event_list():
    try:
        named_events = NamedEvent.objects.filter(is_active=True).order_by("name")
    except Exception as e:
        logger.exception(str(e) + "No named event found")
        return ResponseCode.invalid_argument.value, "No named event found", None

    return (
        ResponseCode.operation_successful.value,
        "Returned Named Events Successfully",
        named_events,
    )


def get_named_event_by_id(id):
    try:
        named_event = NamedEvent.objects.get(is_active=True, id=id)
    except Exception as e:
        logger.exception(str(e) + "No named event found")
        return ResponseCode.invalid_argument.value, "No named event found", None

    return (
        ResponseCode.operation_successful.value,
        "Returned Named Event Successfully",
        named_event,
    )


def get_event_type():
    try:
        event_types = EventType.objects.all().filter(is_active=True)
    except Exception as e:
        logger.exception(str(e) + "No event type found")
        return ResponseCode.invalid_argument.value, "No event type found", None

    return (
        ResponseCode.operation_successful.value,
        "Returned Event Types Successfully",
        event_types,
    )


def get_user_event_dates(user=None, user_events=None):
    event_dates = []
    if not user_events:
        user_events = user.user_events.filter(is_active=True)
    user_events = user_events.values("start_date", "end_date")

    for event in user_events:
        event_dates.extend(
            [_date for _date in daterange(event["start_date"], event["end_date"])]
        )
    return event_dates
