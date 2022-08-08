import copy
import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from drf_yasg.utils import swagger_auto_schema
from requests_oauthlib import OAuth1Session
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from config.emails import email_password_reset_otp
from core.apps.activities.utils import daroan_get_athlete_id
from core.apps.common.common_functions import clear_user_cache
from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.common.enums.response_code import ResponseCode
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    daroan_email_status,
    daroan_login,
    daroan_refresh_token,
    daroan_reset_password,
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.ctp.tasks import create_training_plan
from core.apps.notification.models import UserNotificationSetting
from core.apps.notification.services import PushNotificationSettingService
from core.apps.plan.models import UserPlan
from core.apps.settings.utils import create_initial_settings
from core.apps.user_profile.models import UserActivityLog, UserProfile
from core.apps.utp.utils import update_utp_settings

from ...enums.UserRegistrationTypeEnum import UserRegistrationTypeEnum
from ...models import Otp, UserAuthModel
from ...services import (
    UserAuthService,
    activity_log,
    generate_access_token,
    get_otp_context,
)
from ...swagger_schema import OtpVerificationApiSchema
from ...tokens import account_activation_token
from ...utils import (
    get_user_access_level,
    logging_in_user,
    valid_user_email,
    valid_user_password,
)
from .schema import LoginApiSchemaView

logger = logging.getLogger(__name__)


class EmailStatusView(APIView):
    """Checks if email is already registered or not."""

    secret_key_not_match_msg = "Did not match secret key"

    def post(self, request):
        api_secret_key = request.data.get("api_secret_key")
        if settings.API_SECRET_KEY != api_secret_key:
            return Response(
                make_context(True, self.secret_key_not_match_msg, None),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        email = request.data.get("email").lower()
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                make_context(False, "Invalid Email", None),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        email_status = daroan_email_status(email)

        if not email_status["is_registered"]:
            return Response(make_context(False, "", {"is_email_registered": False}))
        if not email_status["is_active"]:
            return Response(
                make_context(
                    True,
                    "This email has been deactivated. Enter a different email",
                    None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(make_context(False, "", {"is_email_registered": True}))


class UserLoginView(generics.GenericAPIView):
    def post(self, request):
        if settings.API_SECRET_KEY != request.data.get("api_secret_key", None):
            response = make_context(True, "Did not match secret key", None)
            UserActivityLog.objects.create(
                request=request.data,
                response=response,
                activity_code=UserActivityLog.ActivityCode.EMAIL_LOGIN,
            )
            return Response(response)

        email = request.data.get("email", None)
        password = request.data.get("password", None)

        if email is None or password is None:
            response = make_context(True, "Login Credentials Doesn't match", None)
            UserActivityLog.objects.create(
                request=request.data,
                response=response,
                activity_code=UserActivityLog.ActivityCode.EMAIL_LOGIN,
            )
            return Response(response)

        if UserAuthModel.objects.check_login_credentials(email, password):
            try:
                user = UserAuthModel.objects.get(email=email)
                if user.is_email_verified is False:
                    response = make_context(
                        False,
                        "Your email is not verified yet. Please Confirm your mail",
                        None,
                    )
                    UserActivityLog.objects.create(
                        request=request.data,
                        response=response,
                        user_auth=user,
                        user_id=user.code,
                        activity_code=UserActivityLog.ActivityCode.EMAIL_LOGIN,
                    )
                    return Response(response)
                access_token, _ = generate_access_token()
                try:
                    user.access_token = access_token
                    user.save()
                    clear_user_cache(user)
                    response = make_context(
                        False,
                        "User login successful",
                        {"access_token": str(user.access_token)},
                    )
                    UserActivityLog.objects.create(
                        request=request.data,
                        response=response,
                        user_auth=user,
                        user_id=user.code,
                        activity_code=UserActivityLog.ActivityCode.EMAIL_LOGIN,
                    )

                    response["data"]["access_token"] = user.access_token
                    return Response(response)
                except Exception as e:
                    logger.exception(
                        "Falied to login user",
                        extra=log_extra_fields(
                            user_id=user.code,
                            user_auth_id=user.id,
                            exception_message=str(e),
                            service_type=ServiceType.API.value,
                            request_url=request.path,
                        ),
                    )
                    response = make_context(True, "Connection Error", None)
            except UserAuthModel.DoesNotExist:
                response = make_context(True, "No user found with this email", None)
            except Exception as e:
                message = "Falied to login user"
                logger.exception(
                    message,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        service_type=ServiceType.API.value,
                        request_url=request.path,
                    ),
                )
                response = make_context(True, message, None)
        else:
            response = make_context(True, "Login Credentials Doesn't match", None)

        UserActivityLog.objects.create(
            request=request.data,
            response=response,
            activity_code=UserActivityLog.ActivityCode.EMAIL_LOGIN,
        )
        return Response(response)


class LoginView(APIView):

    email_login_activity_code = UserActivityLog.ActivityCode.EMAIL_LOGIN
    user_registration_activity_code = UserActivityLog.ActivityCode.USER_REGISTRATION

    @swagger_auto_schema(request_body=LoginApiSchemaView.request_schema)
    def post(self, request):
        api_secret_key = request.data.get("api_secret_key", None)

        email = request.data.get("email")
        password = request.data.get("password")
        request.data.pop("password")

        if settings.API_SECRET_KEY != api_secret_key:
            response = make_context(True, "Did not match secret key", None)
            activity_log(request, response, self.email_login_activity_code)

            return Response(response)

        if not (valid_user_email(email) and valid_user_password(password)):
            response = make_context(True, "Invalid email/password format", None)
            activity_log(request, response, self.email_login_activity_code)

            return Response(response)

        email = BaseUserManager.normalize_email(email)
        email_status = daroan_email_status(email)
        if email_status["is_registered"] and not email_status["is_active"]:
            return Response(make_context(True, "Email already registered", None))

        if not email_status["is_registered"]:
            # Register User
            try:
                response_data, user = UserAuthService.register_user(email, password)

                UserNotificationSetting.objects.create(
                    user_auth=user, user_id=user.code
                )
                create_initial_settings(user)
                update_utp_settings(
                    user,
                    False,
                    USER_UTP_SETTINGS_QUEUE_PRIORITIES[1],
                    datetime.datetime.now(),
                    reason="new user",
                )

                response = make_context(
                    False, "User created successfully.", response_data
                )
                response = get_user_access_level(response, user)
                activity_log(
                    request, response, self.user_registration_activity_code, user
                )
            except Exception as e:
                logger.exception(
                    "User registration failed",
                    extra=log_extra_fields(
                        request_url=request.path,
                        service_type=ServiceType.API.value,
                        exception_message=str(e),
                    ),
                )

                response = make_context(True, "Error registering user.", str(e))
                activity_log(request, response, self.user_registration_activity_code)
            return Response(response)

        if email_status["is_active"]:
            # Login User
            try:
                daroan_response = daroan_login(
                    email=email,
                    password=password,
                    authentication_secret_key=settings.DAROAN_API_SECRET_KEY,
                )
                logger.info(f"Daroan response = {daroan_response.json()}")
                if daroan_response.status_code != status.HTTP_200_OK:
                    logger.info(
                        f"Daroan login unsuccessful. response {daroan_response.json()}"
                    )
                    message = daroan_response.json()["message"]
                    response = make_context(True, message, None)

                    activity_log(request, response, self.email_login_activity_code)
                    return Response(response, status=status.HTTP_403_FORBIDDEN)

                user = UserAuthModel.objects.get(
                    code=daroan_response.json()["data"]["code"]
                )
                response = logging_in_user(user, daroan_response)
                response = get_user_access_level(response, user)

                clear_user_cache(user)
                activity_log(
                    request, response, UserActivityLog.ActivityCode.EMAIL_LOGIN, user
                )
            except Exception as e:
                message = "Login Failed"
                logger.exception(
                    message,
                    extra=log_extra_fields(
                        request_url=request.path,
                        service_type=ServiceType.API.value,
                        exception_message=str(e),
                    ),
                )
                response = make_context(True, message, None)
                activity_log(request, response, self.email_login_activity_code)
            return Response(response)


class UserRegisterView(APIView):
    def post(self, request):

        if settings.API_SECRET_KEY != request.data.get("api_secret_key", None):
            response = make_context(True, "Did not match secret key", None)
            UserActivityLog.objects.create(
                request=request.data,
                response=response,
                activity_code=UserActivityLog.ActivityCode.USER_REGISTRATION,
            )
            return Response(response)

        reg_type = request.data.get("user_registration_type", None)
        user, response = None, None
        try:
            if reg_type == UserRegistrationTypeEnum.EMAIL_SIGNUP.value:
                response, user = UserAuthService.register_email_user(request)
            elif reg_type == UserRegistrationTypeEnum.STRAVA.value:
                response, user = UserAuthService.register_strava_user(request)
            elif reg_type == UserRegistrationTypeEnum.GARMIN.value:
                response, user = UserAuthService.register_garmin_user(request)
        except Exception as e:
            logger.exception(str(e) + "User creation failed")

        response_copy = copy.deepcopy(response)

        if user:
            update_utp_settings(
                user,
                False,
                USER_UTP_SETTINGS_QUEUE_PRIORITIES[1],
                datetime.datetime.now(),
                reason="new user",
            )
            update_utp_settings(
                user,
                True,
                USER_UTP_SETTINGS_QUEUE_PRIORITIES[2],
                datetime.datetime.now() + datetime.timedelta(hours=48),
                reason="48 hour rule",
            )
            auto_update_settings_status = (
                reg_type != UserRegistrationTypeEnum.EMAIL_SIGNUP.value
            )
            update_utp_settings(
                user,
                auto_update_settings_status,
                USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
                datetime.datetime.now(),
                reason="",
            )

            user_event = user.user_events.filter(is_active=True).last()

            plan = UserPlan(user_auth=user, user_id=user.code, user_event=user_event)
            plan.save()
            create_training_plan(user.id, plan.id, user_event)

            response_copy["data"]["access_token"] = str(
                response_copy["data"]["access_token"]
            )
            UserActivityLog.objects.create(
                request=request.data,
                response=response_copy,
                activity_code=UserActivityLog.ActivityCode.CREATE_TRAINING_PLAN,
                data={"user_plan_id": plan.id},
                user_auth=user,
                user_id=user.code,
            )

        UserActivityLog.objects.create(
            request=request.data,
            response=response_copy,
            user_auth=user,
            activity_code=UserActivityLog.ActivityCode.USER_REGISTRATION,
        )
        return Response(response)

    # /activate/$

    def activate(self, request):
        try:
            uidb64 = request.GET["uid"]
            token = request.GET["token"]
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = UserAuthModel.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserAuthModel.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.is_email_verified = True
            user.save()
            return HttpResponse(
                "Thank you for your email confirmation. Now you can login your account."
            )
        else:
            return HttpResponse("Activation link is invalid!")


class OtpRequestApiView(APIView):
    """
    This api is for sending otp to user email
    """

    sent_otp_msg = (
        "A one time password has been sent to your email. Please check your mail and "
        "submit otp."
    )
    invalid_secret_key_msg = "Did not match secret key"
    user_not_exist_msg = "No user exists with this email"
    wait_one_more_minute = "Please wait one more minute to resend OTP"

    def post(self, request):
        email = request.data.get("email")

        if (
            Otp.objects.smaller_than(settings.OTP_RESEND_MINIMUM_TIME)
            .filter(email__iexact=email)
            .exists()
        ):
            return Response(make_context(True, self.wait_one_more_minute, None))

        res = daroan_get_athlete_id(email)
        if res["error"]:
            return Response(make_context(True, res["message"], None))

        # Delete previously created OTPs
        Otp.objects.filter(email__iexact=email).delete()

        otp_context = get_otp_context(email)
        otp_object = Otp.objects.create(**otp_context)
        user_profile = UserProfile.objects.filter(
            user_id=res["data"]["user_id"], is_active=True
        ).last()
        name = user_profile.name if user_profile else ""

        email_message = render_to_string(
            "reset_password_template.html", {"otp": otp_object.otp, "name": name}
        )
        email_password_reset_otp(email, email_message)
        activity_log(request, otp_context, UserActivityLog.ActivityCode.OTP_REQUEST)

        return Response(
            make_context(
                False,
                self.sent_otp_msg,
                {"otp_verifier_token": otp_object.verifier_token},
            )
        )


class OtpVerificationApiView(APIView):
    """
    This api is for verifying otp
    """

    invalid_otp_msg = "Invalid OTP or has been expired"
    invalid_secret_key_msg = "Did not match secret key"
    success_msg = "Otp access token returned successfully"

    @swagger_auto_schema(
        request_body=OtpVerificationApiSchema.request_schema,
        responses=OtpVerificationApiSchema.responses,
    )
    def post(self, request):
        otp_verifier_token = request.data.get("otp_verifier_token")
        otp = request.data.get("otp")

        otp_object = (
            Otp.objects.smaller_than(settings.OTP_EXPIRATION_TIME)
            .filter(otp=otp, verifier_token=otp_verifier_token)
            .last()
        )
        if not otp_object:
            logger.info("Invalid otp provided")
            return Response(make_context(True, self.invalid_otp_msg, None))

        logger.info("Otp verification successful, saving logs...")
        activity_log(
            request,
            make_context(
                False, self.success_msg, {"otp_access_token": otp_object.access_token}
            ),
            UserActivityLog.ActivityCode.OTP_VERIFICATION,
        )

        return Response(
            make_context(
                False, self.success_msg, {"otp_access_token": otp_object.access_token}
            )
        )


class UserPasswordResetApiView(APIView):
    """
    This api is for changing user password
    """

    invalid_secret_key_msg = "Did not match secret key"
    invalid_otp_token_msg = "OTP access token is invalid or has been expired"
    user_not_exist_msg = "The user you are trying to reset password, no longer exist"
    success_msg = "Your password has been changed successfully. Now you can login to your pillar account."

    def post(self, request):
        otp_access_token = request.data.get("otp_access_token")
        new_password = request.data.get("password")

        otp_object = (
            Otp.objects.smaller_than(settings.OTP_ACCESS_TOKEN_EXPIRATION_TIME)
            .filter(access_token=otp_access_token)
            .last()
        )
        if not otp_object:
            return Response(make_context(True, self.invalid_otp_token_msg, None))

        response = daroan_reset_password(
            email=otp_object.email, new_password=new_password
        )

        if response.status_code != status.HTTP_200_OK:
            logger.info(f"password reset failed, response from daroan {response}")
            return PillarResponse(
                request,
                make_context(True, response.json()["message"], None),
                UserActivityLog.ActivityCode.RESET_PASSWORD,
            )

        otp_object.delete()

        activity_log(
            request,
            make_context(False, self.success_msg, None),
            UserActivityLog.ActivityCode.RESET_PASSWORD,
        )

        return Response(make_context(False, self.success_msg, None))


class RenewAccessTokenView(APIView):
    """This API is used for renewing access token based on provided refresh token"""

    def post(self, request):
        api_secret_key = request.data.get("api_secret_key")

        if settings.API_SECRET_KEY != api_secret_key:
            response = make_context(True, "Did not match secret key", None)
            return Response(response, status=403)

        refresh_token = request.data.get("refresh_token")
        daroan_response = daroan_refresh_token(
            refresh_token=refresh_token,
        )

        error = daroan_response.json().get("error", False)
        message = daroan_response.json().get("message", "")
        data = daroan_response.json().get("data")
        response = make_context(error, message, data)

        return Response(response, status=daroan_response.status_code)


@api_view(["GET"])
def get_garmin_user_activity(request):
    user_access_token = "c86cde0a-466f-4665-9d2d-f0a4390ff6a3"
    user_access_secret = "2cAGH8Cf5FATCN1ezKvIOYJAJBEe4lFga1j"
    callbackURL = "https://healthapi.garmin.com/wellness-api/rest/activityDetails?uploadStartTimeInSeconds=1583685249&uploadEndTimeInSeconds=1583771649"

    client_key = settings.GARMIN_CONSUMER_KEY
    client_secret = settings.GARMIN_CONSUMER_SECRET

    garmin = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=user_access_token,
        resource_owner_secret=user_access_secret,
    )

    response = garmin.get(callbackURL)
    data = json.loads(response.text)
    return data["userId"]


class UserLogOutView(generics.GenericAPIView):
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        fcm_device_token = request.data.get("fcm_device_token")
        PushNotificationSettingService(
            user_auth=user, user_id=user.code
        ).delete_push_notification_setting(fcm_device_token)
        clear_user_cache(user)

        response = make_context(False, "User logout successful", None)
        activity_log(request, response, UserActivityLog.ActivityCode.USER_LOGOUT)

        return Response(response)


@api_view(["POST"])
def add_garmin_info(request):
    response_code, response_message, data = UserAuthService.add_user_garmin_info(
        request
    )
    if response_code != ResponseCode.invalid_argument.value:
        return Response(make_context(False, response_message, data))
    return Response(make_context(True, response_message, data))


@api_view(["POST"])
def get_garmin_activity(request):
    response_code, response_message, data = UserAuthService.add_user_garmin_info(
        request
    )
    if response_code != ResponseCode.invalid_argument.value:
        return Response(make_context(False, response_message, data))
    return Response(make_context(True, response_message, data))


@api_view(["POST"])
def user_garmin_login(request):
    if settings.API_SECRET_KEY != request.data.get("api_secret_key", None):
        response = make_context(True, "Did not match secret key", None)
        UserActivityLog.objects.create(
            request=request.data,
            response=response,
            activity_code=UserActivityLog.ActivityCode.GARMIN_LOGIN,
        )
        return Response(response)

    garmin_id = request.data.get("garmin_user_id", None)
    garmin_token = request.data.get("garmin_user_token", None)
    garmin_user_secret = request.data.get("garmin_user_secret", None)
    access_token, msg, user = UserAuthService.check_garmin_login_and_get_access_token(
        garmin_id, garmin_token, garmin_user_secret
    )

    if access_token is None:
        response = make_context(True, msg, None)
        UserActivityLog.objects.create(
            request=request.data,
            response=response,
            user_auth=user,
            user_id=user.code,
            activity_code=UserActivityLog.ActivityCode.GARMIN_LOGIN,
        )
    else:
        response = make_context(False, msg, {"access_token": str(access_token)})
        UserActivityLog.objects.create(
            request=request.data,
            response=response,
            user_auth=user,
            user_id=user.code,
            activity_code=UserActivityLog.ActivityCode.GARMIN_LOGIN,
        )

        response["data"]["access_token"] = access_token

    return Response(response)


@api_view(["POST"])
def user_garmin_deregistration(request):
    deregistrations = request.data.get("deregistrations", None)
    if deregistrations is None:
        response = make_context(
            True, "'deregistrations' key is not present in the request body", None
        )
        UserActivityLog.objects.create(
            request=request.data,
            response=response,
            activity_code=UserActivityLog.ActivityCode.GARMIN_DEREGISTRATION,
            data={"error": "'deregistrations' key is not present in the request body"},
        )
        return Response(response)

    response = make_context(False, "", None)
    for user_account in deregistrations:
        garmin_user_id = user_account["userId"]
        try:
            user_auth = UserAuthModel.objects.get(
                garmin_user_id=garmin_user_id, is_active=True
            )
        except UserAuthModel.DoesNotExist:
            response = make_context(True, "Garmin ID not found in database", None)
            UserActivityLog.objects.create(
                request=request.data,
                response=response,
                activity_code=UserActivityLog.ActivityCode.GARMIN_DEREGISTRATION,
                data={"garmin_user_id": garmin_user_id},
            )
            continue

        user_auth.garmin_user_token = None
        user_auth.garmin_user_secret = None
        user_auth.save()

        response = make_context(False, "Deleted User Garmin Info from Pillar", None)
        UserActivityLog.objects.create(
            request=request.data,
            response=response,
            user_auth=user_auth,
            user_id=user_auth.code,
            activity_code=UserActivityLog.ActivityCode.GARMIN_DEREGISTRATION,
            data={"garmin_user_id": garmin_user_id},
        )
    return Response(response)
