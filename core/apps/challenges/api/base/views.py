import logging

from django.conf import settings
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response

from core.apps.challenges.api.base.schema import (
    AchievedTrophyApiV1SchemaView,
    ChallengeDescriptionApiV1SchemaView,
    ChallengeOverviewApiV1SchemaView,
    TakeChallengeApiV1SchemaView,
)
from core.apps.challenges.models import Challenge, UserChallenge
from core.apps.challenges.services import ChallengeService
from core.apps.common.common_functions import clear_user_cache
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    log_extra_fields,
    make_context,
)

logger = logging.getLogger(__name__)


class ChallengeOverviewApiV1(generics.GenericAPIView):
    """Return available challenges"""

    success_msg = "Challenge overview data returned successfully"
    error_msg = "Could not retrieve challenge overview data"

    @swagger_auto_schema(responses=ChallengeOverviewApiV1SchemaView.responses)
    def get(self, request):

        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = f"{user.email}:challenge-overview"

        if cache_key in cache and not force_refresh:
            challenges = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, challenges))
        else:
            try:
                challenges = ChallengeService.get_challenge_overview(user)
            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            cache.set(cache_key, challenges, timeout=settings.CACHE_TIME_OUT)

        return Response(
            make_context(False, self.success_msg, challenges), status=status.HTTP_200_OK
        )


class ChallengeDescriptionApiV1(generics.GenericAPIView):
    """Return details of a challenge"""

    success_msg = "Challenge description data returned successfully"
    error_msg = "Could not retrieve challenge description data"

    @swagger_auto_schema(
        request_body=ChallengeDescriptionApiV1SchemaView.request_schema,
        responses=ChallengeDescriptionApiV1SchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        challenge_id = request.data.get("challenge_id")
        challenge_taken = request.data.get("challenge_taken")

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = (
            f"{user.email}:challenge-description:{challenge_id}"
            if not challenge_taken
            else f"{user.email}:my-challenge-description:{challenge_id}"
        )

        if cache_key in cache and not force_refresh:
            challenge_description = cache.get(cache_key)
            return Response(
                make_context(False, self.success_msg, challenge_description)
            )
        else:
            try:
                if challenge_taken:
                    user_challenge = UserChallenge.objects.filter(
                        pk=challenge_id
                    ).last()
                    challenge_description = (
                        ChallengeService.get_current_challenge_details(
                            user, user_challenge
                        )
                    )
                else:
                    challenge = Challenge.objects.filter(pk=challenge_id).last()
                    challenge_description = ChallengeService.get_challenge_description(
                        challenge, user
                    )

            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if not challenge_description.get("bottom_sheet_data"):
                cache.set(
                    cache_key, challenge_description, timeout=settings.CACHE_TIME_OUT
                )

        return Response(
            make_context(False, self.success_msg, challenge_description),
            status=status.HTTP_200_OK,
        )


class TakeChallengeApiV1(generics.GenericAPIView):
    """Return details of a challenge"""

    success_msg = "User Challenge description data returned successfully"
    error_msg = "Could not retrieve challenge description data"

    @swagger_auto_schema(
        request_body=TakeChallengeApiV1SchemaView.request_schema,
        responses=TakeChallengeApiV1SchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        challenge_id = request.data.get("challenge_id")

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = f"{user.email}:challenge-take:{challenge_id}"

        if cache_key in cache and not force_refresh:
            current_challenge_details = cache.get(cache_key)
            return Response(
                make_context(False, self.success_msg, current_challenge_details)
            )
        else:
            try:
                challenge = Challenge.objects.filter(pk=challenge_id).last()
                user_challenge = ChallengeService.take_challenge(user, challenge)
                current_challenge_details = (
                    ChallengeService.get_current_challenge_details(
                        user=user, user_challenge=user_challenge
                    )
                )
                clear_user_cache(user)

            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            cache.set(
                cache_key, current_challenge_details, timeout=settings.CACHE_TIME_OUT
            )

        return Response(
            make_context(False, self.success_msg, current_challenge_details),
            status=status.HTTP_200_OK,
        )


class AchievedTrophyApiV1(generics.GenericAPIView):
    """Shows the achieved challenge trophies"""

    success_msg = "Achieved trophy badges returned successfully"
    error_msg = "Could not retrieve achieved trophy badges"

    @swagger_auto_schema(responses=AchievedTrophyApiV1SchemaView.responses)
    def get(self, request):
        user = get_user_from_session_destroy_session_variable(request)

        force_refresh = True if request.GET.get("force_refresh") == "true" else False
        cache_key = f"{user.email}:achieved-trophy"

        if cache_key in cache and not force_refresh:
            trophies = cache.get(cache_key)
            return Response(make_context(False, self.success_msg, trophies))
        else:
            try:
                trophies = ChallengeService.get_achieved_trophies(user)
            except Exception as e:
                logger.exception(
                    self.error_msg,
                    extra=log_extra_fields(
                        exception_message=str(e),
                        request_url=request.path,
                        user_auth_id=user.id,
                        service_type=ServiceType.API.value,
                    ),
                )
                return Response(
                    make_context(True, self.error_msg, None),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            cache.set(cache_key, trophies, timeout=settings.CACHE_TIME_OUT)

        return Response(
            make_context(False, self.success_msg, trophies), status=status.HTTP_200_OK
        )
