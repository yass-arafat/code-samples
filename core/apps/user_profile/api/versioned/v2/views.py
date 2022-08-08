import datetime
import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import (
    cache_data,
    clear_user_cache_with_prefix,
    pillar_response,
    pro_feature,
)
from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.pillar_responses import PillarResponse
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)
from core.apps.packages.tasks import create_package_plan
from core.apps.packages.utils import create_user_knowledge_hub_entries
from core.apps.plan.models import UserPlan
from core.apps.plan.tasks import create_plan
from core.apps.utp.utils import update_utp_settings

from ....avatar import get_avatar
from ....models import ProfileImage, UserActivityLog, UserProfile
from ....services import AddNewGoalService, save_goal_data
from ....utils import clear_trainer_cache
from .schema import (
    CreateTrainingPlanV2SchemaView,
    UserAvailabilityDataV2ViewSchema,
    UserBasicInfoV2ViewSchema,
    UserFileProcessInfoV2ViewSchema,
    UserFitnessInfoExistV2ViewSchema,
    UserFitnessInfoV2ViewSchema,
    UserOnboardingViewSchema,
    UserSupportSchemaView,
)
from .services import UserProfileServiceV2, UserSupportServiceV2

logger = logging.getLogger(__name__)


class UserBasicInfoViewV2(APIView):
    """Return user basic info like email, joining date etc."""

    success_msg = "Returned User Basic Info Successfully"
    error_msg = "Could not return User Basic Info"

    @swagger_auto_schema(
        tags=UserBasicInfoV2ViewSchema.tags,
        responses=UserBasicInfoV2ViewSchema.responses,
    )
    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        user_id = request.session["user_id"]
        response_data = UserProfileServiceV2(user_id=user_id).get_basic_info()
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)
        return response_data

    @pillar_response()
    def post(self, request):
        user_id = request.session["user_id"]
        timezone = request.data.get("timezone")
        UserProfileServiceV2(user_id=user_id).update_basic_info(
            timezone_id=timezone.get("timezone_id") if timezone else None,
            weight=request.data.get("weight"),
        )
        clear_user_cache_with_prefix(user_id + "&" + request.path, user_id)


class UserFitnessInfoViewV2(APIView):
    """Return user fitness data like ftp, fthr etc."""

    success_msg = "Returned User fitness data Successfully"
    error_msg = "Could not return User fitness data"

    @swagger_auto_schema(
        tags=UserFitnessInfoV2ViewSchema.tags,
        responses=UserFitnessInfoV2ViewSchema.responses,
    )
    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        user_id = request.session["user_id"]
        response_data = UserProfileServiceV2(user_id=user_id).get_current_fitness_data(
            calculate_mhr_from_age=False
        )
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
        clear_trainer_cache(user_id)


class UserFitnessInfoExistViewV2(APIView):
    """Check user fitness data like ftp, fthr etc. exist or not"""

    success_msg = "Returned User fitness exist info Successfully"
    error_msg = "Could not return User fitness data exist info"

    @swagger_auto_schema(
        tags=UserFitnessInfoExistV2ViewSchema.tags,
        request_body=UserFitnessInfoExistV2ViewSchema.request_schema,
        responses=UserFitnessInfoExistV2ViewSchema.responses,
    )
    @cache_data
    def post(self, request, cache_key):
        user_id = request.session["user_id"]
        activity_datetime_str = request.data.get("activity_datetime")
        try:
            response_data = UserProfileServiceV2(
                user_id=user_id
            ).baseline_fitness_exist(activity_datetime_str)

            error, message = False, self.success_msg
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_id=user_id,
                    service_type=ServiceType.API.value,
                ),
            )
            error, message, response_data = True, self.error_msg, None
        return Response(make_context(error=error, message=message, data=response_data))


class UserFileProcessInfoViewV2(APIView):
    """Return user file process info"""

    success_msg = "Returned User file process info Successfully"
    error_msg = "Could not return User file process info"

    @swagger_auto_schema(
        tags=UserFileProcessInfoV2ViewSchema.tags,
        request_body=UserFileProcessInfoV2ViewSchema.request_schema,
        responses=UserFileProcessInfoV2ViewSchema.responses,
    )
    @cache_data
    def post(self, request, cache_key):
        user_id = request.session["user_id"]
        activity_datetime_str = request.data.get("activity_datetime")
        try:
            response_data = UserProfileServiceV2(user_id=user_id).get_file_process_info(
                activity_datetime_str
            )

            error, message = False, self.success_msg
            cache.set(cache_key, response_data, timeout=settings.CACHE_TIME_OUT)
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_id=user_id,
                    service_type=ServiceType.API.value,
                ),
            )
            error, message, response_data = True, self.error_msg, None
        return Response(make_context(error=error, message=message, data=response_data))


class UserTimezoneDataViewV2(APIView):
    """Return user timezone data like timezone name, offset etc."""

    success_msg = "Returned data successfully"
    error_msg = "Could not return User timezone data"

    @swagger_auto_schema(responses=UserAvailabilityDataV2ViewSchema.responses)
    @cache_data
    def get(self, request, cache_key):
        user_id = request.session["user_id"]
        try:
            response_data = UserProfileServiceV2.get_timezone_data()
            data = {"timezones": response_data}

            cache.set(cache_key, data, timeout=settings.CACHE_TIME_OUT)
            return Response(make_context(message=self.success_msg, data=data))
        except Exception as e:
            logger.exception(
                self.error_msg,
                extra=log_extra_fields(
                    exception_message=str(e),
                    request_url=request.path,
                    user_id=user_id,
                    service_type=ServiceType.API.value,
                ),
            )
            return Response(make_context(error=True, message=self.error_msg))


class UserProfileInfoViewV2(generics.GenericAPIView):
    @cache_data
    @pillar_response()
    def get(self, request, **kwargs):
        user_id = request.session["user_id"]
        logger.info("Fetching user profile data")
        user_profile = UserProfile.objects.filter(
            user_id=user_id, is_active=True
        ).last()
        logger.info("Fetching profile image data")
        profile_image = ProfileImage.objects.filter(
            user_id=user_id, is_active=True
        ).first()
        profile_image_url = profile_image.avatar.url if profile_image else get_avatar()

        response_data = {
            "full_name": user_profile.full_name,
            "first_name": user_profile.name,
            "avatar": profile_image_url,
            "threshold_graph_start_date": 1,
        }
        cache.set(kwargs["cache_key"], response_data, timeout=settings.CACHE_TIME_OUT)

        return response_data


class UserOnboardingView(generics.GenericAPIView):
    activity_code = UserActivityLog.ActivityCode.USER_ONBOARDING

    @swagger_auto_schema(
        tags=UserOnboardingViewSchema.tags,
        request_body=UserOnboardingViewSchema.request_schema,
        responses=UserOnboardingViewSchema.responses,
    )
    @pillar_response(activity_code)
    def post(self, request):
        """Gets the onboarding data of a new user and saves them"""
        logger.info("Onboarding API called")
        user_id = request.session["user_id"]
        logger.info(f"{str(user_id)}")

        try:
            response = UserProfileServiceV2.save_user_onboarding_data(
                user_id, request.data
            )
        except Exception as e:
            failed_msg = "Could not save onboarding data"
            logger.exception(
                failed_msg,
                extra=log_extra_fields(
                    user_id=user_id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            response = make_context(True, failed_msg, None)
        return response


class UserPortalOnboardingView(generics.GenericAPIView):
    def post(self, request):
        """Gets the portal onboarding data of a new user and saves them"""
        logger.info("Portal Onboarding API called")
        user_id = request.session["user_id"]
        logger.info(f"{str(user_id)}")

        try:
            response = UserProfileServiceV2.save_user_portal_onboarding_data(
                user_id, request.data
            )
        except Exception as e:
            logger.exception(
                "Could not save portal onboarding data",
                extra=log_extra_fields(
                    user_id=user_id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            response = make_context(True, "Could not save onboarding data", None)
        # TODO seems PillarResponse is not working. Test with PillarResponse and replace Response with confirmation
        # return PillarResponse(user_id, request, response, self.activity_code)
        return Response(response)


class CreateTrainingPlanViewV2(APIView):
    """
    This api is for creating user training plan with given profile data.
    """

    no_user_found_msg = "You are not allowed to create plan"
    data_missing_msg = "Some data needed to create plan are missing"
    success_message = "Saved goal data and created training plan successfully"

    @swagger_auto_schema(
        request_body=CreateTrainingPlanV2SchemaView.request_schema,
        responses=CreateTrainingPlanV2SchemaView.responses,
    )
    @pro_feature
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        user_event_data = request.data.get("event_data")
        user_package_data = request.data.get("package_data")
        user_schedule_data = request.data.get("schedule_data")
        ctp_activity_code = UserActivityLog.ActivityCode.CREATE_TRAINING_PLAN
        try:
            if user_event_data and user_package_data:
                error_message = "Invalid user goal info"
                logger.error(
                    error_message,
                    extra=log_extra_fields(
                        user_id=user.code,
                        user_auth_id=user.id,
                        request_url=request.path,
                        service_type=ServiceType.API.value,
                    ),
                )
                response = make_context(True, error_message, None)
                return PillarResponse(user, request, response, ctp_activity_code)

            user_local_date = user.user_local_date
            if UserPlan.objects.filter(
                user_id=user.code, is_active=True, end_date__gte=user_local_date
            ).exists():
                error_message = "Current goal has not been completed yet"
                logger.error(
                    error_message,
                    extra=log_extra_fields(
                        user_id=user.code,
                        user_auth_id=user.id,
                        request_url=request.path,
                        service_type=ServiceType.API.value,
                    ),
                )
                response = make_context(True, error_message, None)
                return PillarResponse(user, request, response, ctp_activity_code)

            if user.user_plans.filter(is_active=True).exists():
                # If there was a previous goal of the user and it was completed,
                # then goal is created according to the add new goal flow. This is
                # different from the flow that is followed when creating the first goal
                return AddNewGoalService(request, user).add_new_goal()

            if not user:
                logger.info("No allowed user found for create training plan request")
                return PillarResponse(
                    user,
                    request,
                    make_context(True, self.no_user_found_msg, None),
                    ctp_activity_code,
                )

            extra_log_fields = log_extra_fields(
                user_auth_id=user.id,
                service_type=ServiceType.API.value,
                request_url=request.path,
            )

            if not (user_event_data or user_package_data) or not user_schedule_data:
                logger.info(
                    "Some data needed to create plan are missing",
                    extra=extra_log_fields,
                )
                return PillarResponse(
                    user,
                    request,
                    make_context(True, self.data_missing_msg, None),
                    ctp_activity_code,
                )

            goal_data_saved, message = save_goal_data(user, request)

            if not goal_data_saved:
                return PillarResponse(
                    user, request, make_context(True, message, None), ctp_activity_code
                )

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
            logger.info(
                "Updated UTP settings during create training plan",
                extra=extra_log_fields,
            )

            if user_event_data:
                create_plan(user)
            if user_package_data:
                package_id = user_package_data.get("id")
                user_package_duration = user_package_data.get("total_weeks")
                create_package_plan(user.code, package_id, user_package_duration)
                create_user_knowledge_hub_entries(user, package_id)
            response = make_context(False, self.success_message, None)

        except Exception as e:
            msg = "Could not create training plan"
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

        return PillarResponse(user, request, response, ctp_activity_code)


class UserSupportView(APIView):
    """This api is for creating user support ticket"""

    @swagger_auto_schema(
        tags=UserSupportSchemaView.tags,
        request_body=UserSupportSchemaView.request_schema,
        responses=UserSupportSchemaView.responses,
    )
    def post(self, request):
        success_msg = "User support request submitted successfully"
        error_msg = "Could not submit user support request"
        user_support_activity_code = UserActivityLog.ActivityCode.USER_SUPPORT_REQUEST

        """
        post user support message to notion and slack
        """
        user_id = request.session["user_id"]
        log_extra_data = log_extra_fields(
            user_id=user_id,
            service_type=ServiceType.API.value,
            request_url=request.path,
        )

        try:
            UserSupportServiceV2.post_user_support_message(request)
            logger.info(success_msg, extra=log_extra_data)
            response = make_context(False, success_msg, None)
        except Exception as e:
            logger.exception(
                error_msg,
                extra=log_extra_fields(
                    user_id=user_id,
                    exception_message=str(e),
                    service_type=ServiceType.API.value,
                    request_url=request.path,
                ),
            )
            response = make_context(True, error_msg, None)

        # file can't be stored in activity log
        if request.data.get("file") is not None:
            request.data.pop("file")
        if request.data.get("user_log") is not None:
            request.data.pop("user_log")

        return PillarResponse(
            user_id=user_id,
            request=request,
            data=response,
            activity_code=user_support_activity_code,
        )
