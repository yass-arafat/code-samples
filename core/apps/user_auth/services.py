import json
import logging
import random
import time
import uuid

import requests
from django.contrib.auth.hashers import make_password
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.response import Response

from core.apps.common.common_functions import clear_user_cache
from core.apps.common.const import ACCESS_TOKEN_TIMEOUT, REFRESH_TOKEN_TIMEOUT
from core.apps.common.utils import daroan_register_user, log_extra_fields, make_context
from core.apps.event.services import UserEventService
from core.apps.notification.models import UserNotificationSetting
from core.apps.user_profile.models import UserActivityLog, UserProfile
from core.apps.user_profile.services import UserProfileService

from ..common.enums.service_enum import ServiceType
from .enums.UserRegistrationTypeEnum import UserRegistrationTypeEnum
from .models import UserAuthModel
from .tokens import account_activation_token

logger = logging.getLogger(__name__)


class UserAuthService:
    @classmethod
    def register_email_user(cls, request):
        email = request.data["profile_data"]["email"]
        if UserAuthModel.objects.filter(email=email).exists():
            return make_context(True, "Duplicate user", None), None

        password = request.data["profile_data"]["password"]
        if password is None:
            return make_context(True, "Password is None", None), None

        user = create_user(request, email, password)
        if user is None:
            return (
                make_context(
                    True, "Couldn't create user. Internal Connection Error", None
                ),
                user,
            )
        return (
            make_context(
                False, "User created successfully.", {"access_token": user.access_token}
            ),
            user,
        )

    @classmethod
    def register_user(cls, email, password):
        response = daroan_register_user(email=email, password=password)
        if response.status_code != 201:
            raise ValueError(
                f"Failed to save user data in Daroan. Response: {response.json()}"
            )

        response_data = response.json()["data"]
        user = UserAuthModel.objects.create(
            email=email, code=response_data["code"], is_active=True
        )
        response_data.pop("code")
        return response_data, user

    @classmethod
    def register_bulk_email_user(cls, request):
        email = request.data["profile_data"]["email"]
        if UserAuthModel.objects.filter(email=email).exists():
            return

        password = request.data["profile_data"]["password"]
        if password is None:
            return Response(make_context(True, "Password is None", None)), None

        user = create_user(request, email, password)
        if user is None:
            return (
                Response(
                    make_context(
                        True, "Couldn't create user. Internal Connection Error", None
                    )
                ),
                user,
            )
        return (
            Response(
                make_context(
                    False,
                    "User created successfully.",
                    {"access_token": user.access_token},
                )
            ),
            user,
        )

    @classmethod
    def register_garmin_user(cls, request):
        email = request.data["profile_data"]["email"]
        garmin_id = request.data["user_id"]
        garmin_token = request.data["user_token"]
        garmin_secret = request.data["user_secret"]

        if UserAuthModel.objects.filter(
            Q(email=email) | Q(garmin_user_id=garmin_id)
        ).exists():
            return make_context(True, "Duplicate user", None), None

        access_token, user = get_garmin_access_token(
            request, garmin_id, garmin_token, garmin_secret
        )
        if access_token is None:
            return (
                make_context(
                    True, "Couldn't create access token. Internal server error.", None
                ),
                None,
            )
        else:
            return (
                make_context(
                    False,
                    "User Garmin Registration Successful",
                    {"access_token": access_token},
                ),
                user,
            )

    @classmethod
    def register_strava_user(cls, request):
        email = request.data["profile_data"]["email"]
        if UserAuthModel.objects.filter(email=email).exists():
            return make_context(True, "Duplicate user", None), None

        strava_id = request.data["user_id"]
        strava_token = request.data["user_token"]
        access_token, user = get_strava_access_token(request, strava_id, strava_token)

        if access_token is None:
            return (
                make_context(
                    True, "Couldn't create access token. Internal server error.", None
                ),
                None,
            )
        else:
            return (
                make_context(
                    False,
                    "User Strava Registration Successful",
                    {"access_token": access_token},
                ),
                user,
            )

    @classmethod
    def check_garmin_login_and_get_access_token(
        cls, garmin_id, garmin_token, garmin_user_secret
    ):
        try:
            user = UserAuthModel.objects.get(garmin_user_id=garmin_id)
        except Exception as e:
            msg = "No user Found with this id"
            logger.exception(str(e) + msg)
            return None, msg, None
        access_token, _ = generate_access_token()
        user.garmin_user_token = garmin_token
        user.garmin_user_secret = garmin_user_secret
        user.access_token = access_token

        try:
            user.save()
            clear_user_cache(user)
            msg = "User login Successful"
        except Exception as e:
            msg = "Could not save user. Internal server error"
            logger.exception(str(e) + msg)
            return None, msg, user

        return access_token, msg, user


def create_user(request, email, password):
    user = UserAuthModel()
    user.is_active = True
    user.is_email_verified = True
    user.registration_type = UserRegistrationTypeEnum.EMAIL_SIGNUP.value

    user.email = email
    user.access_token, _ = generate_access_token()
    user.password = make_password(password)
    user.save()

    UserNotificationSetting.objects.create(user_auth=user, user_id=user.code)

    try:
        UserProfileService.save_user_profile_data(request, user)
        UserProfileService.save_user_personalise_data(request, user)

        UserEventService.save_user_event_data(request, user)
        UserProfileService.save_user_schedule_data(request, user)
        return user
    except Exception as e:
        logger.error(str(e) + "Could not save user")
        return None


def send_mail(user, request):
    current_site = get_current_site(request)
    mail_subject = "Activate your Pillar account."
    message = render_to_string(
        "acc_active_email.html",
        {
            "user": user,
            "domain": current_site.domain,
            "root_path": request.stream.path,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        },
    )
    to_email = user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()


def get_strava_access_token(request, strava_user_id, strava_user_token):
    access_token, _ = generate_access_token()

    user = save_strava_user(request, strava_user_id, strava_user_token, access_token)
    if user is None:
        return None, None
    else:
        return access_token, user


def get_garmin_access_token(
    request, garmin_user_id, garmin_user_token, garmin_user_secret
):
    access_token, _ = generate_access_token()

    user = save_garmin_user(
        request, garmin_user_id, garmin_user_token, garmin_user_secret, access_token
    )
    if user is None:
        return None, None
    else:
        return access_token, user


def save_strava_user(request, strava_user_id, strava_user_token, access_token):
    try:
        user = UserAuthModel.objects.get(strava_user_id=strava_user_id)
    except UserAuthModel.DoesNotExist:
        user = UserAuthModel()
        user.strava_user_id = strava_user_id
        user.is_active = True
        user.is_email_verified = True
        user.registration_type = UserRegistrationTypeEnum.STRAVA.value

    user.strava_user_token = strava_user_token
    user.access_token = access_token
    user.email = request.data["profile_data"]["email"]
    password = request.data["profile_data"]["password"]
    if password is not None:
        user.password = make_password(password)
    user.save()

    try:
        UserNotificationSetting.objects.create(user_auth=user, user_id=user.code)

        UserProfileService.save_user_profile_data(request, user)
        UserProfileService.save_user_personalise_data(request, user)
        UserProfileService.save_user_schedule_data(request, user)
        UserEventService.save_user_event_data(request, user)
        return user
    except Exception as e:
        logger.error(str(e) + "Could not save strava user")
        return None


def save_garmin_user(
    request, garmin_user_id, garmin_user_token, garmin_user_secret, access_token
):
    try:
        user = UserAuthModel.objects.get(garmin_user_id=garmin_user_id)
    except UserAuthModel.DoesNotExist:
        user = UserAuthModel()
        user.garmin_user_id = garmin_user_id
        user.registration_type = UserRegistrationTypeEnum.GARMIN.value
        user.is_email_verified = True
        user.is_active = True

    user.garmin_user_token = garmin_user_token
    user.garmin_user_secret = garmin_user_secret
    user.access_token = access_token
    user.email = request.data["profile_data"]["email"]
    password = request.data["profile_data"]["password"]
    if password is not None:
        user.password = make_password(password)

    UserNotificationSetting.objects.create(user_auth=user, user_id=user.code)

    try:
        UserProfileService.save_user_profile_data(request, user)
        UserProfileService.save_user_personalise_data(request, user)
        user.save()

        UserEventService.save_user_event_data(request, user)
        UserProfileService.save_user_schedule_data(request, user)
        return user
    except Exception as e:
        logger.error(str(e) + "Could not save user")
        return None


def generate_access_token():
    unique_uuid = uuid.uuid4()
    expiration_time = int(time.time() + ACCESS_TOKEN_TIMEOUT)

    return unique_uuid, expiration_time


def generate_refresh_token():
    refresh_token = uuid.uuid4()
    expiration_time = int(time.time() + REFRESH_TOKEN_TIMEOUT)

    return refresh_token, expiration_time


def get_otp_context(email):
    otp_context = {
        "email": email,
        "verifier_token": str(uuid.uuid4()),
        "access_token": str(uuid.uuid4()),
        "otp": random.randint(100000, 999999),
    }
    return otp_context


def activity_log(request, response, activity_code, user=None):
    user_id = user.code if user else None
    UserActivityLog.objects.create(
        request=request.data,
        response=response,
        activity_code=activity_code,
        user_auth=user,
        user_id=user_id,
    )


class HubspotService:
    @staticmethod
    def get_hubspot_url():
        portal_id = "5311062"
        form_guid = "b9d9f961-949d-44a8-93fa-f20416cd0d4b"
        return f"https://api.hsforms.com/submissions/v3/integration/submit/{portal_id}/{form_guid}"

    @staticmethod
    def get_hubspot_request_data(user_id):
        email = user_id

        user_profile = UserProfile.objects.filter(
            user_id=user_id, is_active=True
        ).last()
        if user_profile is None:
            raise ValueError("User must have at least one active profile")
        name = user_profile.name

        utctime = round(time.time() * 1000)  # time in milliseconds

        json_data = {
            "submittedAt": utctime,
            "fields": [
                {"name": "email", "value": email},
                {"name": "firstname", "value": name},
            ],
            "context": {"pageName": "App Registration"},
            "legalConsentOptions": {
                "consent": {
                    "consentToProcess": True,
                    "text": "I agree to allow Example Company to store and process my personal data.",
                    "communications": [
                        {
                            "value": True,
                            "subscriptionTypeId": 999,
                            "text": "I agree to receive marketing communications from Example Company.",
                        }
                    ],
                }
            },
        }

        return json.dumps(
            json_data
        )  # need to convert to string, otherwise it won't be accepted by hubspot

    @classmethod
    def send_user_data_hubspot(cls, user_id):
        try:
            url = cls.get_hubspot_url()
            headers = {
                "content-type": "application/json",
                "cache-control": "no-cache",
            }

            data_string = cls.get_hubspot_request_data(user_id)

            response = requests.request("POST", url, data=data_string, headers=headers)

            logger.info(
                response.text,
                extra=log_extra_fields(
                    user_id=user_id, service_type=ServiceType.API.value
                ),
            )
        except Exception as e:
            logger.exception(
                "Failed to send user data to hubspot",
                extra=log_extra_fields(
                    user_id=user_id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                ),
            )
