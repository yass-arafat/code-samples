import datetime
import logging

from django.db.models import Sum

from core.apps.challenges.api.base.dictionary import (
    create_challenge_description_dict,
    create_challenge_progress_dict,
    create_challenge_tile_dict,
    create_user_challenge_dict,
    get_achieved_trophy_dict,
    user_challenge_details_dict,
)
from core.apps.challenges.models import Challenge, UserChallenge
from core.apps.common.const import TIME_RANGE_BOUNDARY
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.messages import CHALLENGE_COMPLETION_MESSAGE_BODY
from core.apps.common.utils import log_extra_fields
from core.apps.session.models import ActualSession

logger = logging.getLogger(__name__)


class ChallengeService:
    @staticmethod
    def get_challenge_overview(user):
        """Returns the list of challenges"""
        available_challenges_dict = []
        current_challenges_dict = []

        # adding this challenge__end_date__gte=datetime.date.today() filter for now
        # till there is no dashboard coming for historical challenges
        current_challenges = UserChallenge.objects.filter(
            user_auth=user,
            is_active=True,
            challenge__end_date__gte=datetime.date.today(),
        )
        for current_challenge in current_challenges:
            current_challenges_dict.append(
                create_user_challenge_dict(current_challenge)
            )

        if not current_challenges:
            available_challenges = (
                Challenge.objects.filter(
                    is_active=True, end_date__gte=datetime.date.today()
                )
                .values("id", "title", "badge_url", "summary", "end_date")
                .order_by("id")
            )
            available_challenges_dict = []

            for challenge in available_challenges:
                available_challenges_dict.append(create_challenge_tile_dict(challenge))

        response_dict = {
            "available_challenges": available_challenges_dict,
            "current_challenges": current_challenges_dict,
        }

        return response_dict

    @staticmethod
    def get_challenge_description(challenge, user):
        """Returns description of a challenge"""
        return create_challenge_description_dict(challenge, user)

    @classmethod
    def take_challenge(cls, user, challenge):
        user_today_local_date = DateTimeUtils.get_user_local_date_from_utc(
            user.timezone_offset, datetime.datetime.now()
        )
        (
            achieved_value,
            is_completed,
            completion_date,
        ) = cls.get_challenge_achieved_value(user, challenge, user_today_local_date)
        return UserChallenge.objects.create(
            user_auth=user,
            user_id=user.code,
            challenge=challenge,
            start_date=user_today_local_date,
            achieved_value=achieved_value,
            is_completed=is_completed,
            completion_date=completion_date,
        )

    @staticmethod
    def get_current_challenge_details(user, user_challenge):
        response_dict = {}
        challenge_obj = user_challenge.challenge
        challenge_details_dict = user_challenge_details_dict(
            user_challenge, challenge_obj
        )
        challenge_progress_dict = ChallengeService.get_challenge_progress_data(
            user, challenge_obj
        )
        if user_challenge.is_completed and not user_challenge.completion_message_shown:
            challenge_bottom_sheet = ChallengeService.get_challenge_bottom_sheet_data(
                challenge_obj.title
            )
            user_challenge.completion_message_shown = True
            user_challenge.save()
            response_dict.update(challenge_bottom_sheet)

        response_dict.update(challenge_details_dict)
        response_dict.update(challenge_progress_dict)

        return response_dict

    @staticmethod
    def get_challenge_progress_data(user, challenge):
        date_from, end_date = (
            challenge.start_date,
            challenge.end_date,
        )

        user_local_date = user.user_local_date
        actual_sessions = (
            ActualSession.objects.filter_actual_sessions(
                user_auth=user,
                third_party_id__isnull=False,
                activity_type=ActivityTypeEnum.CYCLING.value[1],
            )
            .filter(session_date_time__date__range=[date_from, user_local_date])
            .order_by("session_date_time")
            .values("session_date_time", "actual_distance_in_meters")
        )

        week_distance_list = []
        interval_start_date = date_from
        interval_end_date = interval_start_date + datetime.timedelta(days=6)

        for i in range(5):
            if interval_start_date < end_date and interval_end_date < end_date:
                week_no = i + 1
                week_distance = actual_sessions.filter(
                    session_date_time__date__range=[
                        interval_start_date,
                        interval_end_date,
                    ]
                ).aggregate(Sum("actual_distance_in_meters"))[
                    "actual_distance_in_meters__sum"
                ]

                week_distance_list.append(
                    create_challenge_progress_dict(
                        week_no,
                        interval_start_date,
                        interval_end_date,
                        week_distance,
                        challenge.unit,
                    )
                )
            elif interval_start_date < end_date:
                week_no = i + 1
                week_distance = actual_sessions.filter(
                    session_date_time__date__range=[
                        interval_start_date,
                        interval_end_date,
                    ]
                ).aggregate(Sum("actual_distance_in_meters"))[
                    "actual_distance_in_meters__sum"
                ]

                week_distance_list.append(
                    create_challenge_progress_dict(
                        week_no,
                        interval_start_date,
                        end_date,
                        week_distance,
                        challenge.unit,
                    )
                )
            else:
                break
            interval_start_date = interval_end_date + datetime.timedelta(days=1)
            interval_end_date = interval_start_date + datetime.timedelta(days=6)

        return {"progress": week_distance_list}

    @staticmethod
    def get_challenge_bottom_sheet_data(title):
        return {
            "bottom_sheet_data": {
                "title": title + " Badge Earned",
                "body": CHALLENGE_COMPLETION_MESSAGE_BODY,
            }
        }

    @staticmethod
    def get_achieved_trophies(user):
        trophies = []
        achieved_challenges = UserChallenge.objects.filter(
            user_auth=user, is_active=True, is_completed=True
        ).values(
            "challenge__title",
            "challenge__badge_url",
            "challenge__target_value",
            "challenge__unit",
            "completion_date",
        )
        for achieved_challenge in achieved_challenges:
            trophies.append(get_achieved_trophy_dict(achieved_challenge))

        return {"trophies": trophies}

    @staticmethod
    def update_user_challenge_data(user, actual_session):
        """Updates the user_challenge table for current actual session"""
        extra_log_fields = log_extra_fields(
            user_auth_id=user.id, service_type=ServiceType.INTERNAL.value
        )
        logger.info("User challenge data update process starts", extra=extra_log_fields)

        # Check if duplicate session from lower priority third party exists
        start_time = actual_session.session_date_time - datetime.timedelta(
            seconds=TIME_RANGE_BOUNDARY
        )
        end_time = actual_session.session_date_time + datetime.timedelta(
            seconds=TIME_RANGE_BOUNDARY
        )
        actual_sessions = ActualSession.objects.filter(
            user_auth=actual_session.user_auth,
            session_date_time__range=(start_time, end_time),
            is_active=True,
        ).exclude(id=actual_session.id)
        if actual_session.session_code:
            session = (
                actual_sessions.filter(session_code=actual_session.session_code)
                .order_by("third_party__priority")
                .first()
            )
        else:
            session = (
                actual_sessions.filter(session_code__isnull=True)
                .order_by("third_party__priority")
                .first()
            )

        if (
            session is None
            or actual_session.third_party.priority < session.third_party.priority
        ):
            # As of R10, a user can have only one active challenge. Still the user_challenges variable is taken as
            # plural and a loop is used so that in future it is possible to add support for multiple active challenges
            # with minimal changes

            user_challenges = UserChallenge.objects.filter(
                user_auth=user,
                is_active=True,
                challenge__start_date__lte=actual_session.session_date_time,
                challenge__end_date__gte=actual_session.session_date_time.date(),
            )

            for user_challenge in user_challenges:
                achieved_value = user_challenge.achieved_value
                if session:
                    # Subtract the lower priority session's value from challenge's achieved value before updating with
                    # current actual_session's value
                    achieved_value -= session.actual_distance_in_meters

                # Take the challenge type from an enum when more than one challenge type is introduced
                # As of R10 only "DISTANCE" type challenge is available

                # if user_challenge.challenge.challenge_type == "DISTANCE":
                user_challenge.achieved_value = (
                    achieved_value + actual_session.actual_distance_in_meters
                )
                if (
                    user_challenge.achieved_value
                    >= user_challenge.challenge.target_value * 1000
                ):  # Convert target distance into meters
                    user_challenge.is_completed = True
                    user_challenge.completion_date = datetime.date.today()
                user_challenge.save()
                logger.info(
                    f"User challenge id: {user_challenge.id} of user: {user.id} updated"
                )

        logger.info("User challenge data update process ends")

    @classmethod
    def update_user_challenge_data_task(cls, user):
        """Updates all the current challenge data of user"""

        today = datetime.date.today()
        current_challenges = UserChallenge.objects.filter(
            user_auth=user,
            is_active=True,
            challenge__start_date__lte=today,
            challenge__end_date__gte=today,
        )

        for user_challenge in current_challenges:
            (
                achieved_value,
                is_completed,
                completion_date,
            ) = cls.get_challenge_achieved_value(user, user_challenge.challenge)
            user_challenge.achieved_value = achieved_value
            if not user_challenge.is_completed and is_completed:
                user_challenge.is_completed = is_completed
                user_challenge.completion_date = completion_date

            user_challenge.save()

    @staticmethod
    def get_challenge_achieved_value(user, challenge, user_today_local_date):
        """Returns the achieved value of a particular challenge and checks if the challenge is completed"""
        achieved_value = list(
            ActualSession.objects.filter_actual_sessions(
                user_auth=user,
                third_party_id__isnull=False,
                activity_type=ActivityTypeEnum.CYCLING.value[1],
            )
            .filter(
                session_date_time__date__range=[
                    challenge.start_date,
                    user_today_local_date,
                ]
            )
            .aggregate(Sum("actual_distance_in_meters"))
            .values()
        )[0]
        if not achieved_value:
            achieved_value = 0
        if (
            achieved_value and achieved_value >= challenge.target_value * 1000
        ):  # Convert target value to meters from km
            is_completed = True
            completion_date = user_today_local_date
        else:
            is_completed = False
            completion_date = None

        return achieved_value, is_completed, completion_date
