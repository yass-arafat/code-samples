import logging
from datetime import datetime, timedelta

from core.apps.common.const import (
    AVERAGE_HEART_RATE_BOUNDARY,
    AVERAGE_POWER_BOUNDARY,
    MAX_AVERAGE_SPEED,
    MAX_SESSION_DISTANCE,
    MAX_SESSION_DURATION,
    UTC_TIMEZONE,
)
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.date_time_format_enum import DateTimeFormatEnum
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.tp_common_tasks import calculate_curve_data
from core.apps.common.tp_common_utils import (
    get_third_party_instance,
    same_session_date_time_exists,
)
from core.apps.common.utils import create_new_model_instance, log_extra_fields
from core.apps.evaluation.daily_evaluation.utils import set_actual_day_data
from core.apps.evaluation.session_evaluation.utils import (
    calculate_session,
    check_overtraining,
)
from core.apps.notification.enums.notification_type_enum import NotificationTypeEnum
from core.apps.notification.services import (
    create_notification,
    get_activity_notification_attributes,
)
from core.apps.plan.enums.session_status_enum import (
    SessionLabelTypeEnum,
    SessionTypeEnum,
)
from core.apps.user_profile.utils import get_user_fthr, get_user_ftp

from ...achievements.tasks import update_user_achievements
from ...challenges.tasks import update_user_challenge
from ...session.services import SessionPairingService
from ..services import ReevaluationService
from .utils import (
    add_manual_data_to_model,
    calculate_manual_activity_data,
    create_manual_activity_data_instance,
    get_average_speed_from_ride_summary,
)

logger = logging.getLogger(__name__)


class ActivityObject:
    def __init__(self):
        self.elapsed_time = 0
        self.average_power = 0.0
        self.average_heart_rate = 0.0
        self.average_speed = 0.0
        self.total_power = 0.0
        self.total_heart_rate = 0.0
        self.distance = 0.0
        self.moving_time = 0.0
        self.weighted_power = 0.0
        self.activity_type = None


class ManualActivityService:
    @classmethod
    def get_manual_activity_input(cls, request, user):
        timezone_offset = user.timezone_offset or UTC_TIMEZONE
        activity_name = request.data.get("activity_name")
        manual_activity_type = request.data.get("activity_type")
        activity_type = ActivityTypeEnum.get_pillar_defined_activity_name(
            activity_type=manual_activity_type
        )
        activity_label = request.data.get("activity_label")
        activity_duration = request.data.get("activity_duration")
        activity_distance = request.data.get("activity_distance")
        average_speed = request.data.get("average_speed")
        activity_date = request.data.get("activity_date")
        activity_start_time = request.data.get("activity_start_time")
        date_time = activity_date + " " + activity_start_time
        activity_date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
        utc_activity_date_time = DateTimeUtils.get_utc_date_time_from_local_date_time(
            timezone_offset=timezone_offset, local_date_time=activity_date_time
        )

        average_heart_rate = request.data.get("average_heart_rate")
        average_power = request.data.get("average_power")
        effort_level = request.data.get("effort_level", False)

        # Below paragraph is depreciated from R8 and onwards
        stress_level = request.data.get("stress_level", False)
        if stress_level:
            effort_level = stress_level

        activity_description = request.data.get("activity_description")

        activity_distance *= (
            1000  # Km distance input converted into meter for manual activity input
        )

        return {
            "activity_name": activity_name,
            "activity_type": activity_type,
            "activity_label": activity_label,
            "activity_duration": activity_duration,
            "activity_distance": activity_distance,
            "average_speed": average_speed,
            "activity_date": activity_date,
            "activity_date_time": activity_date_time,
            "utc_activity_date_time": utc_activity_date_time,
            "average_heart_rate": average_heart_rate,
            "average_power": average_power,
            "effort_level": effort_level,
            "activity_description": activity_description,
        }

    @classmethod
    def input_validation(
        cls,
        activity_type,
        activity_label,
        activity_duration,
        activity_distance,
        average_speed,
        activity_date,
        activity_date_time,
        average_heart_rate,
        average_power,
        activity_name,
        user,
    ):
        """Checks if manual activity request data are valid or not"""

        if len(activity_name) > 30:
            return (
                True,
                "Activity name is longer than max character limit (Max limit: 30 characters)",
                None,
            )
        if not (activity_type.lower() in SessionTypeEnum.lower()):
            return True, f"Invalid Activity Type: {activity_type}", None
        if not (activity_label.lower() in SessionLabelTypeEnum.lower()):
            return True, f"Invalid Activity Label: {activity_label}", None

        if (not activity_duration) or (activity_duration > MAX_SESSION_DURATION):
            return True, f"Invalid activity duration: {activity_duration}", None
        if (not activity_distance) or (activity_distance > MAX_SESSION_DISTANCE):
            return True, "Invalid activity distance", None
        if (not average_speed) or (average_speed > MAX_AVERAGE_SPEED):
            return True, "Invalid average speed", None

        if not activity_date:
            return True, "No activity date was provided", None
        if same_session_date_time_exists(
            activity_date_time, user, ThirdPartySources.MANUAL.value[0]
        ):
            logger.info(
                "A manual activity with same session date time already exists",
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    user_id=user.code,
                    service_type=ServiceType.INTERNAL.value,
                ),
            )
            return (
                True,
                "A manual activity with same session date time already exists",
                None,
            )

        if average_heart_rate and (
            average_heart_rate < AVERAGE_HEART_RATE_BOUNDARY["lowest"]
            or average_heart_rate > AVERAGE_HEART_RATE_BOUNDARY["highest"]
        ):
            return True, "Please enter a viable Average Heart Rate value", None
        if average_power and (
            average_power < AVERAGE_POWER_BOUNDARY["lowest"]
            or average_power > AVERAGE_POWER_BOUNDARY["highest"]
        ):
            return True, "Please enter a viable Average Power value", None

        return False, "All inputs are validated successfully", None

    @classmethod
    def record_manual_activity(cls, user, input_obj, planned_id=None):
        """Validates the inputs for manual activity, performs calculation and records the data in the database"""

        error, msg, data = cls.input_validation(
            input_obj["activity_type"],
            input_obj["activity_label"],
            input_obj["activity_duration"],
            input_obj["activity_distance"],
            input_obj["average_speed"],
            input_obj["activity_date"],
            input_obj["activity_date_time"],
            input_obj["average_heart_rate"],
            input_obj["average_power"],
            input_obj["activity_name"],
            user,
        )

        if not error:
            activity_obj = create_manual_activity_data_instance(
                input_obj["activity_duration"],
                input_obj["activity_distance"],
                input_obj["average_power"],
                input_obj["average_speed"],
                input_obj["average_heart_rate"],
                input_obj["activity_type"],
            )

            activity_data = add_manual_data_to_model(
                activity_obj=activity_obj,
                user_auth=user,
                activity_type=input_obj["activity_type"],
                activity_date_time=input_obj["activity_date_time"],
            )

            error, msg, data = calculate_manual_activity_data(
                user,
                activity_obj,
                input_obj["activity_date_time"],
                input_obj["utc_activity_date_time"],
                activity_data,
                planned_id,
                input_obj["effort_level"],
                input_obj["activity_description"],
                input_obj["activity_name"],
                input_obj["activity_label"],
            )

        return error, msg, data


class ThirdPartyActivityService:
    @classmethod
    def process_athlete_activity(cls, user_auth, activities):
        logger.info(f"Calculating session of user {user_auth.id}")
        for index, activity in enumerate(activities):
            logger.info(f"Starting to process {index} {activity}")
            try:
                logger.info("Try started")
                activity_datetime = datetime.strptime(
                    activity["local_start_time"],
                    DateTimeFormatEnum.date_time_format.value,
                )
                utc_activity_datetime = datetime.strptime(
                    activity["start_time"], DateTimeFormatEnum.date_time_format.value
                )
                third_party_code = ThirdPartySources.get_code_from_text(
                    activity["source"]
                )
                logger.info("same session checking started")
                if same_session_date_time_exists(
                    activity_datetime, user_auth, third_party_code
                ):
                    logger.info(
                        "An activity with same session date time already exists",
                        extra=log_extra_fields(
                            user_auth_id=user_auth.id,
                            user_id=user_auth.code,
                            service_type=ServiceType.INTERNAL.value,
                        ),
                    )
                    continue
                logger.info("Creating third-party object")
                third_party_data = ActivityObject()
                third_party_data.elapsed_time = activity["elapsed_time"]
                third_party_data.moving_time = activity["moving_time"]
                third_party_data.distance = activity["distance"]
                third_party_data.total_heart_rate = activity["total_heart_rate"]
                third_party_data.average_heart_rate = activity["average_heart_rate"]
                third_party_data.total_power = activity["total_power"]
                third_party_data.average_power = activity["average_power"]
                third_party_data.weighted_power = activity["weighted_power"]

                logger.info("Third-party object creation done")

                average_speed = get_average_speed_from_ride_summary(
                    activity["ride_summary"]
                )

                user_ftp = get_user_ftp(user_auth, activity_datetime)
                user_fthr = get_user_fthr(user_auth, activity_datetime)
                logger.info("fetched ftp and fthr")
                actual_session, planned_today, actual_yesterday = calculate_session(
                    user_auth,
                    user_ftp,
                    user_fthr,
                    activity_datetime,
                    utc_activity_datetime,
                    third_party_data,
                )
                logger.info("Calculated actual session")
                third_party_code = ThirdPartySources.get_code_from_text(
                    activity["source"]
                )
                actual_session.third_party = get_third_party_instance(third_party_code)
                actual_session.activity_type = activity["type"]
                actual_session.elevation_gain = activity["elevation_gain"]

                logger.info(f"AthleteActivity code: {activity['code']}")
                actual_session.athlete_activity_code = activity["code"]
                logger.info(
                    f"ActualSession athlete_activity_code: {actual_session.athlete_activity_code}"
                )

                actual_session.reason = "Third party file process"
                actual_session.save()

                logger.info(
                    f"Saved Actual Session. Activity time: {actual_session.session_date_time}"
                )
                logger.info(
                    f"ActualSession athlete_activity_code: {actual_session.athlete_activity_code}"
                )

                logger.info("Calculating Curve Data")
                calculate_curve_data.delay(user_auth.id, user_auth.code, activity)
                logger.info("Curve Data Calculation Complete")

                # Check if current session's third party has higher priority. If yes then check if same activity from a
                # different third party is already synced and paired with the planned session of that day.
                # If yes then unpair the previous actual session and pair the current one
                if actual_session.is_highest_priority_session():
                    same_actual_session = (
                        actual_session.get_sessions_in_timerange_boundary().last()
                    )
                    if same_actual_session and same_actual_session.session_code:
                        logger.info(
                            "Same session from different third party is already paired"
                        )
                        session_code = same_actual_session.session_code
                        planned_session = same_actual_session.planned_session
                        SessionPairingService.unpair_actual_session(same_actual_session)
                        SessionPairingService.pair_actual_session(
                            planned_session, actual_session, session_code, user_auth
                        )

                actual_today = set_actual_day_data(planned_today, actual_session)
                if actual_today:
                    if actual_today.created_at:
                        actual_today = create_new_model_instance(actual_today)
                        actual_today.reason = "Third party file process"
                    actual_today.save()

                    if (
                        planned_today
                        and actual_session.activity_type
                        == ActivityTypeEnum.CYCLING.value[1]
                    ):
                        logger.info("Checking Overtraining")
                        check_overtraining(
                            actual_session, actual_yesterday, planned_today, user_auth
                        )

                # Send notification only if there are no other session in the same
                # timerange
                if not actual_session.get_sessions_in_timerange_boundary().exists():
                    (
                        notification_title,
                        notification_body,
                        data,
                    ) = get_activity_notification_attributes(
                        activity["type"], activity_datetime.date(), actual_session.code
                    )
                    create_notification(
                        user_auth,
                        NotificationTypeEnum.NEW_ACTIVITY,
                        notification_title,
                        notification_body,
                        data,
                    )

                logger.info("Start updating user achievement and challenge data")
                update_user_achievements(user_auth, actual_session, average_speed)
                update_user_challenge(user_auth, actual_session)

                start_date = activity_datetime.date()
                if activity["code"] == activities[-1]["code"]:
                    logger.info("Reevaluation started")
                    ReevaluationService.reevaluate_session_data(
                        user_auth, start_date, start_date + timedelta(days=1)
                    )
                    break

                next_activity_start_date = datetime.strptime(
                    activities[index + 1]["start_time"],
                    DateTimeFormatEnum.date_time_format.value,
                ).date()
                if start_date + timedelta(days=1) < next_activity_start_date:
                    end_date = next_activity_start_date - timedelta(days=1)
                    ReevaluationService.reevaluate_session_data(
                        user_auth, start_date, end_date
                    )
                logger.info("Finally !!!!!!")
            except Exception as e:
                logger.exception(
                    "Failed to calculate session.",
                    extra=log_extra_fields(
                        exception_message=str(e),
                        user_auth_id=user_auth.id,
                        service_type=ServiceType.INTERNAL.value,
                    ),
                )
