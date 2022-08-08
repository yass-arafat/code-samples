import logging
from decimal import Decimal

from core.apps.calculations.evaluation.acute_load_services import AcuteLoadService
from core.apps.calculations.evaluation.load_services import LoadService
from core.apps.calculations.evaluation.prs_services import PrsService
from core.apps.calculations.evaluation.session_accuracy_score_services import (
    SessionAccuracyScoreService as SASService,
)
from core.apps.calculations.evaluation.sqs_services import (
    SqsTodayService,
    WeightingSqsService,
)
from core.apps.common.common_functions import get_actual_day_yesterday
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.utils import (
    create_new_model_instance,
    get_obj_recovery_index,
    log_extra_fields,
)
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.plan.enums.session_status_enum import SessionTypeEnum
from core.apps.session.models import ActualSession, PlannedSession, SessionScore
from core.apps.session.utils import flag_unusual_load_sqs_drop

from .api.base.serializers import (
    ActualDayPrsSerializer,
    DailyTargetPrsObjSerializer,
    PlannedDayLoadSerializer,
)
from .models import DailyTargetPrsObj

logger = logging.getLogger(__name__)


def get_event_target_prs(user_event, goal_status):
    if not user_event:
        return None, None
    event_type_details = user_event.event_type.details
    if goal_status == "Complete":
        target_lower_prs = event_type_details.complete_lower_target_prs
        target_upper_prs = event_type_details.complete_upper_target_prs
    elif goal_status == "Compete":
        target_lower_prs = event_type_details.compete_lower_target_prs
        target_upper_prs = event_type_details.compete_upper_target_prs
    else:  # goal_status == 'Podium':
        target_lower_prs = event_type_details.podium_lower_target_prs
        target_upper_prs = event_type_details.podium_upper_target_prs
    return round(target_lower_prs), round(target_upper_prs)


def get_previous_sessions_pss(sessions):
    previous_sessions_pss = 0
    for sess in sessions:
        if sess.zone_focus == 0:
            continue
        previous_sessions_pss += sess.actual_pss if sess.actual_pss else 0

    return previous_sessions_pss


def set_recovery_day_values(recovery_session, actual_sessions, actual_day):
    session_score = SessionScore()

    if actual_sessions.filter(
        session_code=None
    ):  # Only recovery session in recovery day
        session_score.pss_score = 1
        session_score.duration_score = 1
        session_score.sqs_session_score = 1
        session_score.overall_score = 1
    else:
        session_score.pss_score = 7
        session_score.duration_score = 7
        session_score.sqs_session_score = 7
        session_score.overall_score = 7

    session_score.prs_score = actual_day.prs_score
    session_score.save()

    recovery_session.session_score = session_score
    return recovery_session


def get_daily_prs(onboarding_date, utc_today_date, user):
    actual_day_list = ActualDay.objects.filter(
        activity_date__range=(onboarding_date, utc_today_date),
        user_auth=user,
        is_active=True,
    ).order_by("activity_date")
    serialized = ActualDayPrsSerializer(
        actual_day_list, many=True, context={"offset": user.timezone_offset}
    )
    return serialized.data


def get_days_planned_load(user, onboarding_date, today):
    try:
        actual_day_list = PlannedDay.objects.filter(
            user_auth=user,
            activity_date__range=(onboarding_date, today),
            is_active=True,
        ).order_by("activity_date")
        serialized = PlannedDayLoadSerializer(
            actual_day_list,
            many=True,
            context={
                "offset": user.profile_data.filter(is_active=True)
                .first()
                .timezone.offset
            },
        )
    except Exception as e:
        logger.exception(
            str(e)
            + "No planned load data from onboarding to today found in PlannedDay for the user"
        )
        return []
    return serialized.data


def get_daily_target_prs(
    onboarding_date_according_to_user_local_date,
    event_date_according_to_user_local_date,
    starting_prs,
    target_lower_prs,
    target_upper_prs,
):
    onboarding_prs = DailyTargetPrsObj(
        date=onboarding_date_according_to_user_local_date,
        lower_target_prs=starting_prs,
        upper_target_prs=starting_prs,
    )

    event_day_target_prs = DailyTargetPrsObj(
        date=event_date_according_to_user_local_date,
        lower_target_prs=target_lower_prs,
        upper_target_prs=target_upper_prs,
    )
    daily_target_prs = [onboarding_prs, event_day_target_prs]

    serialized = DailyTargetPrsObjSerializer(daily_target_prs, many=True)
    return serialized.data


def day_midnight_calculation(user_auth, activity_date):
    try:
        actual_day = ActualDay.objects.get(
            user_auth=user_auth, activity_date=activity_date, is_active=True
        )
    except ActualDay.DoesNotExist:
        return
    # if not recovery day, no midnight calculation will occur
    if actual_day.zone_focus != 0:
        return

    try:
        try:
            planned_recovery_session = PlannedSession.objects.get(
                session_date_time__date=activity_date,
                user_auth=user_auth,
                is_active=True,
            )
        except PlannedSession.DoesNotExist:
            return
        actual_sessions = ActualSession.objects.filter(
            session_date_time__date=activity_date, user_auth=user_auth, is_active=True
        )
        try:
            actual_recovery_session = actual_sessions.get(
                session_code=planned_recovery_session.session_code
            )
        except ActualSession.DoesNotExist:
            actual_recovery_session = ActualSession()
            actual_recovery_session.user_auth = user_auth
            actual_recovery_session.user_id = user_auth.code
            actual_recovery_session.day_code = actual_day.day_code
            actual_recovery_session.session_date_time = actual_day.activity_date
            actual_recovery_session.session_code = planned_recovery_session.session_code
            actual_recovery_session.activity_type = (
                SessionTypeEnum.RECOVERY.value.lower()
            )
        else:
            actual_recovery_session = create_new_model_instance(actual_recovery_session)

        actual_recovery_session = set_recovery_day_values(
            actual_recovery_session, actual_sessions, actual_day
        )

        actual_recovery_session.save()

        if flag_unusual_load_sqs_drop(user_auth, activity_date):
            logger.info(
                f"Actual load or SQS changed more than change limit \
                            for {user_auth.id} at {activity_date} when running day_midnight_calculation"
            )

        return actual_day

    except Exception as e:
        logger.exception(
            "Midnight calculation failed",
            extra=log_extra_fields(
                user_auth_id=user_auth.id,
                service_type=ServiceType.INTERNAL.value,
                exception_message=str(e),
            ),
        )

        if flag_unusual_load_sqs_drop(user_auth, activity_date):
            logger.info(
                f"Actual load or SQS changed more than change limit \
                            for {user_auth.id} at {activity_date} when running day_midnight_calculation"
            )


def day_morning_calculation(user_auth, calculation_date):
    try:
        planned_day = PlannedDay.objects.filter(
            user_auth=user_auth, activity_date=calculation_date, is_active=True
        ).last()
        actual_day = ActualDay.objects.filter(
            user_auth=user_auth, activity_date=calculation_date, is_active=True
        ).last()
        if not actual_day:
            actual_day = ActualDay(
                user_auth=user_auth,
                activity_date=calculation_date,
                user_id=user_auth.code,
            )
        else:
            actual_day = create_new_model_instance(actual_day)
        actual_day.set_data_from_planned_day(planned_day)

        day_yesterday, is_onboarding_day = get_actual_day_yesterday(
            user_auth, calculation_date
        )

        actual_day.actual_pss = 0

        load_service = LoadService(
            load_yesterday=day_yesterday.actual_load, pss_today=actual_day.actual_pss
        )
        actual_day.actual_load = Decimal(load_service.get_load_today(is_onboarding_day))

        acute_load_service = AcuteLoadService(
            acute_load_yesterday=day_yesterday.actual_acute_load,
            pss_today=actual_day.actual_pss,
        )
        actual_day.actual_acute_load = Decimal(
            acute_load_service.get_acute_load_today(is_onboarding_day)
        )

        actual_day.recovery_index = get_obj_recovery_index(actual_day)

        sqs_today_service = SqsTodayService(day_yesterday.sqs_today, 0)
        actual_day.sqs_today = sqs_today_service.get_sqs_today(actual_day.zone_focus)

        w_sqs_service = WeightingSqsService(actual_day.sqs_today)
        w_sqs = w_sqs_service.get_weighting_sqs()

        prs_service = PrsService(
            actual_day.actual_load, actual_day.recovery_index, w_sqs
        )
        actual_day.prs_score = prs_service.get_prs()

        actual_day.sas_today = SASService.calculate_sas_today(
            sas_yesterday=day_yesterday.sas_today,
            overall_accuracy_score=None,
            zone_focus=actual_day.zone_focus,
        )

        weighting_sas = SASService.calculate_weighting_sas(actual_day.sas_today)
        prs_score_service = PrsService(
            actual_day.actual_load, actual_day.recovery_index, weighting_sas
        )
        actual_day.prs_accuracy_score = prs_score_service.get_prs()
        actual_day.reason = "day_morning_calculation function call"

        actual_day.save()

        if flag_unusual_load_sqs_drop(user_auth, calculation_date):
            logger.info(
                f"Actual load or SQS changed more than change limit "
                f"for {user_auth.id} at {calculation_date} when running day_morning_calculation"
            )

        return actual_day

    except Exception as e:
        logger.exception(
            "Morning calculation Failed",
            extra=log_extra_fields(
                user_auth_id=user_auth.id,
                service_type=ServiceType.INTERNAL.value,
                exception_message=str(e),
            ),
        )

        if flag_unusual_load_sqs_drop(user_auth, calculation_date):
            logger.info(
                f"Actual load or SQS changed more than change limit "
                f"for {user_auth.id} at {calculation_date} when running day_morning_calculation"
            )


def set_actual_day_data(planned_day_obj=None, actual_session=None):
    if not actual_session.is_highest_priority_session():
        return None
    if planned_day_obj:
        actual_day_obj = ActualDay.objects.filter(
            day_code=planned_day_obj.day_code, is_active=True
        ).last()
    else:
        actual_day_obj = ActualDay.objects.filter(
            activity_date=actual_session.session_date_time.date(),
            user_auth=actual_session.user_auth,
            is_active=True,
        ).last()
    if not actual_day_obj:
        actual_day_obj = ActualDay(
            user_auth=actual_session.user_auth,
            user_id=actual_session.user_auth.code,
            activity_date=actual_session.session_date_time.date(),
        )
        actual_day_obj.set_data_from_planned_day(planned_day_obj)

    actual_day_obj.set_data_from_actual_session(actual_session)
    return actual_day_obj
