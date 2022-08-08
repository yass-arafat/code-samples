import datetime
import logging

import requests
from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import (
    cache_data,
    clear_user_cache,
    clear_user_cache_with_prefix,
    pillar_response,
    pro_feature,
)
from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.common.date_time_utils import convert_str_date_time_to_date_time_obj
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    dakghor_backfill_request,
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.plan.tasks import create_plan
from core.apps.settings.models import UserSettings
from core.apps.settings.user_settings_type_codes import SettingsCode
from core.apps.settings.utils import update_push_notification_settings
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_auth.services import HubspotService
from core.apps.utp.tasks import update_user_training_plan_for_changing_availability
from core.apps.utp.utils import update_utp_settings

from ...avatar import get_avatar
from ...models import ProfileImage, TimeZone, UserActivityLog, UserProfile
from ...services import (
    ActivityLogsService,
    AddNewGoalService,
    UserInfoService,
    UserProfileService,
    save_profile_data,
    save_user_metadata,
)
from ...utils import get_user_starting_values, update_user_baseline_fitness_request
from ..versioned.v2.services import UserProfileServiceV2
from .schema import (
    CreateTrainingPlanSchemaView,
    PushNotificationSettingsApiSchemaView,
    UserActivityLogsApiSchemaView,
    UserMetadataApiSchemaView,
)
from .serializers import (
    ProfileImageSerializer,
    ProfileImageSerializer2,
    UserInfoSerializer,
    UserSettingsSerializer,
)
from .services import PersonaliseDataService

logger = logging.getLogger(__name__)


class UserProfileView(generics.GenericAPIView):
    activity_code = UserActivityLog.ActivityCode.USER_PROFILE_UPDATE

    @pillar_response()
    def post(self, request):
        user_id = request.session["user_id"]
        UserInfoService(request).update_user_info()
        clear_user_cache_with_prefix(user_id + "&" + request.path, user_id)


class UserSettingsView(generics.GenericAPIView):
    activity_code = UserActivityLog.ActivityCode.USER_PROFILE_UPDATE

    def get(self, request):
        user_code = request.session["user_id"]
        user_profile = UserProfile.objects.filter(
            user_id=user_code, is_active=True
        ).first()

        clear_user_cache(user_id=str(user_code))
        if user_profile is None:
            return Response(make_context(True, "User settings not found", None))
        else:
            force_refresh = (
                True if request.GET.get("force_refresh") == "true" else False
            )
            cache_key = str(user_code) + ":" + "user_settings_info"

            if cache_key in cache and not force_refresh:
                cached_data = cache.get(cache_key)
                return Response(
                    make_context(
                        False,
                        "Returned user settings successfully",
                        cached_data.data["settings_data"],
                    )
                )
            else:
                context = {
                    "user_subscription_status": request.session[
                        "user_subscription_status"
                    ],
                    "user_code": str(user_code),
                    "timezone_offset": user_profile.timezone.offset,
                }
                try:
                    serialized = UserSettingsSerializer(user_profile, context=context)
                    data = serialized.data["settings_data"]
                except Exception as e:
                    error_message = "Failed to fetch user settings"
                    logger.exception(
                        error_message,
                        extra=log_extra_fields(
                            user_id=user_code,
                            service_type=ServiceType.API.value,
                            exception_message=str(e),
                            request_url=request.path,
                        ),
                    )
                    return Response(make_context(True, error_message, None))
                cache.set(cache_key, data, timeout=settings.CACHE_TIME_OUT)
                return Response(
                    make_context(False, "Returned user settings successfully", data)
                )


class TimeZoneView(generics.GenericAPIView):
    activity_code = UserActivityLog.ActivityCode.USER_PROFILE_UPDATE

    def get(self, request):
        pass

    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        timezone_id = request.data.get("timezone_id", None)
        try:
            previous_timezone = user.profile_data.timezone.offset
            current_timezone = TimeZone.objects.get(
                id=timezone_id, is_active=True
            ).offset
            UserProfileService.run_cron_for_timezone_change(
                user, previous_timezone, current_timezone
            )
        except Exception as e:
            logger.info("Timezone Change API" + str(e))

        error, msg = UserProfileService.save_timezone_to_profile(
            timezone_id, user.profile_data.filter(is_active=True).first()
        )
        response = make_context(error, msg, None)
        clear_user_cache(user)

        return PillarResponse(user, request, response, self.activity_code)


class PushNotificationSettingsView(generics.GenericAPIView):
    @swagger_auto_schema(
        responses=PushNotificationSettingsApiSchemaView.get_api_responses
    )
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        try:
            data = {
                "is_push_notification_enabled": UserSettings.objects.get(
                    user_auth=user,
                    code=SettingsCode.PUSH_NOTIFICATION_SETTINGS_CODE,
                    is_active=True,
                ).status
            }

            response = make_context(
                False, "Returned push notification settings successfully", data
            )
        except Exception as e:
            msg = "Failed to fetch push notification settings."
            logger.exception(
                msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                ),
            )

            response = make_context(True, msg, None)

        return Response(response)

    @swagger_auto_schema(
        request_body=PushNotificationSettingsApiSchemaView.request_schema,
        responses=PushNotificationSettingsApiSchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        try:
            is_push_notification_enabled = request.data.get(
                "is_push_notification_enabled"
            )
            user_push_notification_setting = UserSettings.objects.get(
                user_auth=user,
                code=SettingsCode.PUSH_NOTIFICATION_SETTINGS_CODE,
                is_active=True,
            )
            if user_push_notification_setting.status != is_push_notification_enabled:
                update_push_notification_settings(
                    user_setting=user_push_notification_setting,
                    status=is_push_notification_enabled,
                    updated_by="user",
                    reason="api",
                )

            error, msg = False, "Saved push notification settings successfully"
        except Exception as e:
            error, msg = True, "Failed to save push notification settings"
            logger.exception(
                msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                ),
            )
        return Response(make_context(error, msg, None))


class UserProfilePictureView(generics.GenericAPIView):
    activity_code = UserActivityLog.ActivityCode.USER_PROFILE_PICTURE_UPDATE

    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        user_id = request.session["user_id"]

        profile_image = ProfileImage.objects.filter(
            user_id=user_id, is_active=True
        ).first()
        if profile_image:
            is_placeholder_image = False
            profile_image_url = profile_image.avatar.url

        else:
            is_placeholder_image = True
            profile_image_url = get_avatar()
        data = {
            "is_placeholder_image": is_placeholder_image,
            "url": profile_image_url,
        }
        cache.set(kwargs["cache_key"], data, timeout=settings.CACHE_TIME_OUT)
        return data

    @pillar_response()
    def post(self, request):
        user_id = request.session["user_id"]
        profile_image = ProfileImage.objects.filter(
            user_id=user_id, is_active=True
        ).first()
        profile_image_serializer = ProfileImageSerializer2(data=request.data)

        if profile_image_serializer.is_valid():
            if profile_image:
                profile_image.is_active = False
                profile_image.save()

            new_profile_image = profile_image_serializer.save(
                user_id=user_id, is_active=True
            )
            serialized = ProfileImageSerializer(new_profile_image)

            clear_user_cache_with_prefix(user_id + "&" + request.path, user_id)
            return serialized.data

    @pillar_response()
    def delete(self, request):
        user_id = request.session["user_id"]
        profile_image = ProfileImage.objects.filter(
            user_id=user_id, is_active=True
        ).first()
        profile_image.delete()
        clear_user_cache_with_prefix(user_id + "&" + request.path, user_id)


class UserTrainingAvailabilityView(generics.GenericAPIView):
    activity_code = UserActivityLog.ActivityCode.USER_TRAINING_AVAILABILITY_UPDATE
    success_message = (
        "Your training plan has been updated to fit around your future availability, "
        "as a result some of your scheduled sessions may have changed. "
    )

    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        try:
            logger.info(
                "Update training availability",
                extra=log_extra_fields(
                    request_url=request.path,
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                ),
            )
            (
                user_training_availability,
                msg,
            ) = UserProfileService.save_user_schedule_data(request, user)
            today = datetime.datetime.today()
            user_active_training_plan = user.user_plans.filter(
                is_active=True, end_date__gte=today
            ).last()
            if user_active_training_plan:
                update_user_training_plan_for_changing_availability(
                    user.id, user_training_availability.id
                )
            success_msg = "User Training Availability Saved Successfully"
            response = make_context(False, success_msg, self.success_message)
            logger.info(
                success_msg,
                extra=log_extra_fields(
                    request_url=request.path,
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                ),
            )
        except Exception as e:
            error_msg = "Couldn't save User Training Availability"
            response = make_context(True, error_msg, str(e))
            logger.exception(
                error_msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_auth_id=user.id,
                    service_type=ServiceType.API.value,
                ),
            )

        return PillarResponse(user, request, response, self.activity_code)


class CreateTrainingPlan(APIView):
    """
    This api is for creating user training plan with given profile data.
    """

    no_user_found_msg = "You are not allowed to create plan"
    profile_data_missing_msg = "Missing some profile data to create plan successfully"
    success_message = "Saved user profile and created training plan successfully"

    @swagger_auto_schema(request_body=CreateTrainingPlanSchemaView.request_schema)
    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        user_profile_data = request.data.get("profile_data")
        user_event_data = request.data.get("event_data")
        user_personalise_data = request.data.get("personalise_data")
        user_schedule_data = request.data.get("schedule_data")
        ctp_activity_code = UserActivityLog.ActivityCode.CREATE_TRAINING_PLAN

        if not user:
            return PillarResponse(
                user,
                request,
                make_context(True, self.no_user_found_msg, None),
                ctp_activity_code,
            )

        if (
            not user_profile_data
            or not user_event_data
            or not user_personalise_data
            or not user_schedule_data
        ):
            return PillarResponse(
                user,
                request,
                make_context(True, self.profile_data_missing_msg, None),
                ctp_activity_code,
            )

        saved_profile, message = save_profile_data(user, request)

        if not saved_profile:
            return PillarResponse(
                user, request, make_context(True, message, None), ctp_activity_code
            )

        if settings.HUBSPOT_ENABLE:
            HubspotService.send_user_data_hubspot(user)

        update_utp_settings(
            user,
            True,
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[2],
            datetime.datetime.now() + datetime.timedelta(hours=48),
            reason="48 hour rule",
        )

        update_utp_settings(
            user,
            user.is_third_party_connected(),
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[3],
            datetime.datetime.now(),
            reason="",
        )

        create_plan(user)
        dakghor_backfill_request(
            source=ThirdPartySources.GARMIN.value[1].lower(), athlete_id=user.id
        )
        # dakghor_backfill_request(source=ThirdPartySources.STRAVA.value[1].lower(), athlete_id=user.id)

        return PillarResponse(
            user,
            request,
            make_context(False, self.success_message, None),
            ctp_activity_code,
        )


class UserInfoView(generics.GenericAPIView):
    serializer_class = UserInfoSerializer

    def post(self, request):
        if settings.EMAIL_MICROSERVICE_SECRET_KEY != request.data.get(
            "email_ms_secret_key", None
        ):
            msg = "Did not match secret key"
            logger.info(msg)
            logger.info(request.data.get("email_ms_secret_key"))
            return Response(make_context(True, msg, None))

        serialized = UserInfoSerializer(UserAuthModel.objects.get_users(), many=True)
        return Response(
            make_context(False, "Returned User Info Successfully", serialized.data)
        )


class UserPersonaliseDataApiView(APIView):
    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        user_id = request.session["user_id"]
        activity_datetime_str = request.data.get("activity_datetime")
        activity_datetime = convert_str_date_time_to_date_time_obj(
            activity_datetime_str
        )

        response_data = PersonaliseDataService(user_id=user_id).get_personalise_data(
            activity_datetime=activity_datetime
        )
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)

        return response_data


class UserPersonaliseDataListApiView(APIView):
    @pillar_response()
    def get(self, request):
        user_id = request.session["user_id"]
        return PersonaliseDataService(user_id).get_personalise_data_list()


class UserCurrentPersonaliseDataApiView(APIView):
    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        user_id = request.session["user_id"]

        response_data = PersonaliseDataService(
            user_id=user_id
        ).get_current_personalise_data()
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)

        return response_data

    @pillar_response()
    def post(self, request):
        user_id = request.session["user_id"]
        personalise_data = request.data.get("personalise_data")
        PersonaliseDataService(user_id=user_id).save_current_personalise_data(
            ftp=personalise_data.get("ftp"),
            training_hours_over_last_4_weeks=personalise_data.get(
                "training_hours_over_last_4_weeks"
            ),
            threshold_heart_rate=personalise_data.get("threshold_heart_rate"),
            max_heart_rate=personalise_data.get("max_heart_rate"),
        )

        clear_user_cache_with_prefix(prefix=user_id, user_id=user_id)


class AddNewGoalApiView(APIView):
    no_user_found_msg = "User not found"
    event_data_not_found_msg = "User event data not provided"
    user_goal_exist_msg = "User already have an active goal"
    success_message = "Created new user goal and created training plan successfully"
    no_previous_goal_msg = (
        "You are trying to add a new goal but it seems that you dont have"
        " completed any goal yet"
    )
    no_personalise_data_msg = (
        "Date since last goal is more than 3 and no personalise data provided"
    )
    add_new_goal_activity_code = UserActivityLog.ActivityCode.ADD_NEW_GOAL

    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        try:
            return AddNewGoalService(request, user).add_new_goal()
        except Exception as e:
            msg = "Could not add new goal"
            logger.exception(
                msg,
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            response = make_context(True, msg, None)
        return PillarResponse(user, request, response, self.add_new_goal_activity_code)


class UserBaselineFitnessView(APIView):

    """This api will return user baseline fitness data on a specific time"""

    @cache_data
    @pillar_response()
    def post(self, request, **kwargs):
        user_id = request.session["user_id"]
        activity_datetime_str = request.data.get("activity_datetime")

        logger.info(f"activity_datetime_str = {activity_datetime_str}")

        response_data = UserProfileServiceV2(user_id=user_id).get_fitness_data(
            activity_datetime_str
        )
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)

        return response_data


class UserBaselineFitnessDateRangeView(APIView):

    """This api will return user baseline fitness data for a specific time period"""

    @cache_data
    @pillar_response()
    def post(self, request, **kwargs):
        user_id = request.session["user_id"]
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        response_data = UserProfileServiceV2(
            user_id=user_id
        ).get_fitness_data_in_daterange(start_date, end_date)
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)

        return response_data


class UserCurrentBaselineFitnessView(APIView):
    """This api will return current/latest baseline fitness data"""

    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        user_id = request.session["user_id"]
        response_data = UserProfileServiceV2(user_id=user_id).get_current_fitness_data()
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)
        return response_data

    @pillar_response()
    def post(self, request):
        user_id = request.session["user_id"]
        UserProfileServiceV2(user_id=user_id).save_fitness_info(
            ftp=request.data.get("ftp"),
            fthr=request.data.get("fthr"),
            mhr=request.data.get("mhr"),
        )

        clear_user_cache_with_prefix(prefix=user_id, user_id=user_id)


class UserBaselineFitnessRequestView(generics.GenericAPIView):
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        try:
            response_data = update_user_baseline_fitness_request(user, request)
            clear_user_cache(user)
            return Response(
                make_context(False, "Saved Data Successfully", response_data)
            )
        except Exception as e:
            message = "Couldn't save data"
            logger.exception(f"{message}. Exception: {str(e)}")
            return Response(make_context(True, message, None))


class AthletesInfoApiView(APIView):
    def post(self, request):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        athlete_ids = request.data.get("athlete_ids")

        athletes_info = UserProfileService.get_athletes_info(athlete_ids)
        return Response(
            make_context(False, "Athletes info returned successfully", athletes_info)
        )


class UserMetadataApiView(APIView):
    """
    This api is to update user metadata e.g. device model, hash, app version
    """

    @swagger_auto_schema(
        request_body=UserMetadataApiSchemaView.request_schema,
        responses=UserMetadataApiSchemaView.responses,
    )
    @pillar_response()
    def post(self, request):
        build_number = request.data.get("build_number", False)
        device_info = request.data.get("device_info", False)
        hash_value = request.data.get("hash_value", False)

        logger.info("saving user meta data")

        save_user_metadata(
            build_number=build_number,
            device_info=device_info,
            hash_value=hash_value,
            user_id=request.session["user_id"],
        )


class UserActivityLogsApiView(generics.GenericAPIView):
    """
    This api is to update user metadata e.g. device model, hash, app version
    """

    @swagger_auto_schema(
        request_body=UserActivityLogsApiSchemaView.request_schema,
        responses=UserActivityLogsApiSchemaView.responses,
    )
    def post(self, request):
        logger.info("Received activity logs")
        activity_logs = request.data.get("activity_logs")
        ActivityLogsService.save_user_activity_logs(activity_logs)
        return Response(
            make_context(False, "Activity logs received successfully", None)
        )


class SubscriptionAPIView(generics.GenericAPIView):
    def post(self, request):
        print(datetime.datetime.now())
        print(request.data)
        return Response(
            make_context(False, "Received Successfully", None),
            status=status.HTTP_200_OK,
        )


class PaymentSyncAPIView(generics.GenericAPIView):
    def post(self, request):
        print(f"Payment-sync api invoked with body {request.data}")
        app_user_id = request.data.get("app_user_id")
        # payment_status = request.data.get("status")

        RC_API_KEY = "swFCDflVmPMWbLhRJHivxSiTswtcMKkX"

        headers = {
            "Authorization": f"Bearer {RC_API_KEY}",
        }
        url = f"https://api.revenuecat.com/v1/subscribers/{app_user_id}"
        response = requests.get(url, headers=headers)

        logger.info(f"User RC info: {response}")
        logger.info(f"User RC json info: {response.json()}")
        entitlements = response.json().get("subscriber").get("entitlements")

        if "pillar_stag_pro" in entitlements:
            err, msg, data, httpstatus = (
                False,
                "Subscription Successful",
                {"is_subscription_active": True},
                status.HTTP_200_OK,
            )
        elif not ("pillar_stag_pro" in entitlements):
            err, msg, data, httpstatus = (
                False,
                "Subscription Cancellation Successful",
                {"is_subscription_active": False},
                status.HTTP_200_OK,
            )
        else:
            err, msg, data, httpstatus = (
                True,
                "Subscription  Unsuccessful",
                None,
                status.HTTP_402_PAYMENT_REQUIRED,
            )

        return Response(
            make_context(err, msg, data=data),
            status=httpstatus,
        )


class UserTimeZoneView(APIView):
    """Returns the time zone offset of a user"""

    success_msg = "User time zone offset returned successfully"
    error_msg = "Could not return user time zone offset data"

    def get(self, request):
        user_code = request.session["user_id"]
        try:
            logger.info(f"fetching user profile for user {user_code}")
            user_profile = UserProfile.objects.filter(
                user_id=user_code, is_active=True
            ).last()
            logger.info(
                f"Returning timezone_offset for user {user_code} data {user_profile.timezone.offset}"
            )
            return Response(
                make_context(
                    message=self.success_msg,
                    data={"user_timezone_offset": user_profile.timezone.offset},
                )
            )
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    user_id=user_code, exception_message=f"Exception message: {e}"
                ),
            )

            return Response(
                make_context(
                    error=True,
                    message=self.error_msg,
                )
            )


class TimeZoneUserView(APIView):
    """Returns user-ids of given time zone offset"""

    @pillar_response()
    def post(self, request, **kwargs):
        timezone_offset = request.data.get("timezone_offset")
        logger.info(f"fetching user ids for timezone {timezone_offset}")
        user_ids = list(
            UserProfile.objects.filter(
                timezone__offset=timezone_offset, is_active=True, user_id__isnull=False
            ).values_list("user_id", flat=True)
        )

        return {"user_ids": user_ids}


class UserStartingValuesView(APIView):
    """Returns the time zone offset of a user"""

    def get(self, request):
        user_id = request.session["user_id"]
        user_starting_values = get_user_starting_values(user_id)

        return Response(
            make_context(
                False,
                "User starting values returned successfully",
                user_starting_values,
            )
        )


class UserFirstHistoryInputDateView(APIView):
    @pillar_response()
    def get(self, request):
        user_id = request.session.get("user_id")
        return {
            "history_input_date": UserProfileService(
                user_id=user_id
            ).get_first_history_input_date()
        }


class ClearUserCacheView(APIView):
    @pillar_response()
    def get(self, request):
        user_id = request.session["user_id"]
        clear_user_cache_with_prefix(prefix=user_id, user_id=user_id)
