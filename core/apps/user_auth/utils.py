import logging

from django.contrib.auth.password_validation import validate_password
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.apps.activities.utils import dakghor_get_athlete_info
from core.apps.common.utils import get_user_metadata_hash, make_context

from .tokens import account_activation_token

logger = logging.getLogger(__name__)


def send_password_reset_email(request, user):
    current_site = get_current_site(request)
    mail_subject = "Reset Password Email"
    # TODO: this template doesn't exist
    message = render_to_string(
        "acc_reset_password_email.html",
        {
            "user": user,
            "domain": current_site.domain,
            "root_path": "/api/v1/auth/",
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        },
    )
    to_email = user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    try:
        email.send()
    except Exception as e:
        logger.exception(str(e))


# TODO: no need for this function
def logging_in_user(user, daroan_response):
    """Logs in a registered user"""
    response_data = daroan_response.json()["data"]
    response_data.pop("code")
    response_data["user_metadata_hash"] = get_user_metadata_hash(user)

    response = make_context(False, "User login successful", data=response_data)
    return response


def get_user_access_level(response, user):
    # TODO: Refactor this function so that it doesn't need the response parameter
    """Returns the current access level of the user"""
    # TODO: FILTER ONLY ONE FIELD
    user_profile = user.profile_data.filter(is_active=True).last()
    response["data"]["access_level"] = (
        user_profile.access_level if user_profile else "PROFILE"
    )
    user_info = dakghor_get_athlete_info(user.id)
    response["data"]["is_garmin_connected"] = user_info["is_garmin_connected"]
    response["data"]["is_strava_connected"] = user_info["is_strava_connected"]
    response["data"]["is_wahoo_connected"] = user_info["is_wahoo_connected"]

    return response


def valid_user_email(email):
    """Checks if the email is of valid format"""
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def valid_user_password(password):
    """Checks if the password is of valid format"""
    try:
        validate_password(password)
        return True
    except ValidationError:
        return False
