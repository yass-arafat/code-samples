import logging
from datetime import datetime, timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.const import LOWEST_PLAN_LENGTH, UTC_TIMEZONE
from core.apps.common.enums.response_code import ResponseCode
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    make_context,
)

from ...enums.event_sub_type_enum import EventSubTypeEnum
from ...enums.event_type_enum import EventTypeEnum
from ...models import NamedEvent
from ...services import get_event_type, get_named_event_by_id, get_named_event_list
from .serializers import EventNameSerializer, EventTypeSerializer, NamedEventSerializer

logger = logging.getLogger(__name__)


class NamedEventListView(APIView):
    def get(self, request):
        """Returns a list of all the active events."""
        user = get_user_from_session_destroy_session_variable(request)
        event_type_name = request.GET.get("event_type")
        event_type_value = EventTypeEnum.get_code_from_serialized_name(event_type_name)

        minimum_event_start_date = datetime.now() + timedelta(days=LOWEST_PLAN_LENGTH)
        named_event_list = NamedEvent.objects.filter(
            is_active=True,
            start_date__gte=minimum_event_start_date,
            event_type__type=event_type_value,
        ).order_by("name")

        serializer = EventNameSerializer(
            named_event_list, context={"offset": user.timezone_offset}, many=True
        )
        named_event_list_data = serializer.data
        error = False

        if not named_event_list_data:
            msg = "Could not get any event."
            return Response(make_context(error, msg, named_event_list_data))

        msg = "Event list returned successfully"
        return Response(make_context(error, msg, named_event_list_data))


class NamedEventDetailView(APIView):
    def get(self, request, event_id):
        """Returns the event of given event_id"""
        try:
            user = get_user_from_session_destroy_session_variable(request)
            named_event = NamedEvent.objects.get(is_active=True, id=event_id)
            serializer = NamedEventSerializer(named_event, context={"user": user})
            named_event_data = serializer.data
            msg = "Named Event returned successfully"
            error = False
        except NamedEvent.DoesNotExist as e:
            msg = "Could not get Named Event"
            error = True
            named_event_data = None
            logger.exception(str(e) + msg)

        return Response(make_context(error, msg, named_event_data))


@api_view(["GET"])
def get_named_event(request, event_id):
    offset = request.GET.get("timezone", UTC_TIMEZONE)
    response_code, response_message, data = get_named_event_by_id(event_id)

    if response_code == ResponseCode.operation_successful.value:
        serialize = NamedEventSerializer(data, context={"offset": offset})

        return Response(make_context(False, response_message, serialize.data))
    else:
        return Response(make_context(True, response_message, data))


@api_view(["GET"])
def get_name_list_of_named_event(request):
    response_code, response_message, data = get_named_event_list()

    if response_code == ResponseCode.operation_successful.value:
        serialized = EventNameSerializer(data, many=True)
        return Response(make_context(False, response_message, serialized.data))
    else:
        return Response(make_context(True, response_message, data))


@api_view(["GET"])
def get_predefined_type_list_event(request):
    response_code, response_message, data = get_event_type()

    if response_code == ResponseCode.operation_successful.value:
        serialized = EventTypeSerializer(data, many=True)
        return Response(make_context(False, response_message, serialized.data))
    else:
        return Response(make_context(True, response_message, data)) @ api_view(["GET"])


@api_view(["GET"])
def get_type_of_event(request):
    data = []
    for x in EventTypeEnum:
        list = {"event_type_name": x.value[1]}
        data.append(list)
    return Response(make_context(False, "Returned Event type SuccessFully", data))


@api_view(["GET"])
def get_sub_type_of_event(request):
    data = []
    for x in EventSubTypeEnum:
        list = {"event_type_name": x.value[1]}
        data.append(list)
    return Response(make_context(False, "Returned Event type SuccessFully", data))
