import logging

import requests
from log_request_id import local

from core.apps.common.enums.dakghor_urls_enum import DakghorURLEnum
from core.apps.common.enums.daroan_urls_enum import DaroanURLEnum
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import log_extra_fields, make_context

logger = logging.getLogger(__name__)


def recalculate_single_day(user_auth, actual_sessions, _date):
    from core.apps.evaluation.daily_evaluation.utils import day_morning_calculation
    from core.apps.evaluation.session_evaluation.utils import recalculate_sessions

    actual_day = day_morning_calculation(user_auth, _date)
    today_actual_sessions = actual_sessions.filter(
        session_date_time__date=actual_day.activity_date
    )
    recalculate_sessions(user_auth, actual_day, today_actual_sessions)


def dakghor_get_athlete_activity(athlete_activity_code):
    url = DakghorURLEnum.ATHLETE_ACTIVITY.value
    return requests.post(
        url=url, json={"athlete_activity_code": str(athlete_activity_code)}
    )


def dakghor_get_athlete_info(user_code):
    url = DakghorURLEnum.ATHLETE.value
    response = requests.post(url=url, json={"athlete_code": str(user_code)}).json()
    logger.info(f"Dakghor response {response}")
    return response["data"]["athlete"]


def daroan_get_athlete_info(user_id):
    url = DaroanURLEnum.USER_INFO.value
    logger.info("Fetching data from daroan")
    try:
        response = requests.post(
            url=url,
            json={"user_id": str(user_id)},
        ).json()
        logger.info(f"Daroan response {response}")
    except Exception as e:
        logger.exception(
            "Error when fetching data from daroan",
            extra=log_extra_fields(
                user_id=user_id,
                service_type=ServiceType.API.value,
                exception_message=str(e),
            ),
        )
        response = make_context(error=True)

    return response


def daroan_get_athlete_id(email):
    url = DaroanURLEnum.USER_ID.value + f"?email={email}"
    logger.info(f"Fetching user id from daroan = {url}")
    try:
        response = requests.get(
            url=url,
            headers={"Correlation-Id": local.request_id},
        ).json()
        logger.info(f"Daroan response {response}")
    except Exception as e:
        logger.exception(
            "Error when fetching data from daroan",
            extra=log_extra_fields(
                service_type=ServiceType.API.value,
                exception_message=str(e),
            ),
        )
        response = make_context(error=True)

    return response
