import json
import logging

import requests
from django.conf import settings
from django.core import serializers
from django_rq import job

from core.apps.common.enums.trainer_urls import TrainerURLEnum
from core.apps.daily.models import PlannedDay
from core.apps.session.models import PlannedSession

logger = logging.getLogger(__name__)


@job
def send_mail(from_email, to_email, template_code):
    url = settings.EMAIL_MS_BASE_URL + "api/v1/emails/send-immediate-mail"
    request = {
        "email_ms_api_secret_key": settings.EMAIL_MICROSERVICE_SECRET_KEY,
        "from_email": from_email,
        "to_email": to_email,
        "template_code": template_code,
    }

    response = requests.post(url=url, json=request)
    if response.status_code != 200 or response.status_code != 201:
        logger.error(
            f"Could not send mail from {from_email} to {to_email}. Exception = {response.text}"
        )
    else:
        logger.info(f"Email sent successfully from {from_email} to {to_email}")


def migrate_planned_data_to_trainer(user_auth):
    serializer_format = "json"
    planned_sessions = PlannedSession.objects.filter(user_auth=user_auth)
    serialized_sessions = serializers.serialize(serializer_format, planned_sessions)

    planned_days = PlannedDay.objects.filter(user_auth=user_auth)
    serialized_days = serializers.serialize(serializer_format, planned_days)

    payload = {
        "api_secret_key": settings.TRAINER_API_SECRET_KEY,
        "planned_sessions": json.loads(serialized_sessions),
        "planned_days": json.loads(serialized_days),
    }
    url = TrainerURLEnum.DATA_MIGRATE.value
    response = requests.post(url=url, json=payload)

    assert (
        response.status_code != 200
    ), f"Data migration failed. Response: {json.dumps(response.json())}"
