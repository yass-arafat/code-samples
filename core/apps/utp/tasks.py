import datetime
import logging

from celery import shared_task
from django_rq import job

from core.apps.common.common_functions import (
    clear_user_cache,
    get_auto_update_start_datetime,
    get_timezone_offset_from_datetime_diff,
)
from core.apps.common.const import FIRST_TIMEZ0NE_OFFSET
from core.apps.common.date_time_utils import time_diff_between_two_timezone_offsets
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.models import CronHistoryLog
from core.apps.common.utils import create_new_model_instance, log_extra_fields
from core.apps.packages.services import UpdatePackagePlan
from core.apps.plan.models import UserPlan
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.models import UserActivityLog, UserTrainingAvailability
from core.apps.week.models import UserWeek

from .services import UpdateTrainingPlan
from .utils import get_data_details_dict, is_user_valid_for_auto_update

logger = logging.getLogger(__name__)


@job
def update_user_training_plan(user_id):
    try:
        user = UserAuthModel.objects.get(id=user_id, is_active=True)
    except UserAuthModel.DoesNotExist:
        return

    try:
        user_plan = UserPlan.objects.filter(user_auth=user, is_active=True).last()

        if user_plan.user_event_id:
            UpdateTrainingPlan(user).run_auto_update_for_weeks()
        if user_plan.user_package_id:
            UpdatePackagePlan(user).run_auto_update_for_weeks()
    except Exception as e:
        logger.exception(
            "UTP failed",
            extra=log_extra_fields(
                exception_message=str(e),
                user_auth_id=user_id,
                service_type=ServiceType.INTERNAL.value,
            ),
        )
        cron_status = CronHistoryLog.StatusCode.FAILED
    else:
        clear_user_cache(user)
        cron_status = CronHistoryLog.StatusCode.SUCCESSFUL

    CronHistoryLog.objects.create(
        cron_code=CronHistoryLog.CronCode.AUTO_UPDATE_TRAINING_PLAN,
        user_auth=user,
        user_id=user.code,
        status=cron_status,
    )


@job
def update_user_training_plan_for_changing_availability(
    user_id, training_availability_id
):
    logger.info(
        "Updating user training plan",
        extra=log_extra_fields(
            user_auth_id=user_id, service_type=ServiceType.INTERNAL.value
        ),
    )
    try:
        user = UserAuthModel.objects.get(id=user_id, is_active=True)
        training_availability = UserTrainingAvailability.objects.get(
            pk=training_availability_id
        )
        schedule_start_date = training_availability.start_date.date()
        user_weeks_to_update = UserWeek.objects.filter(
            user_block__user_auth=user,
            end_date__gte=schedule_start_date,
            is_active=True,
        ).order_by("start_date")
        try:
            user_plan = UserPlan.objects.filter(user_auth=user, is_active=True).last()

            if user_plan.user_event_id:
                UpdateTrainingPlan(
                    user, user_weeks_to_update, schedule_start_date
                ).run_auto_update_for_weeks()
            if user_plan.user_package_id:
                UpdatePackagePlan(
                    user, user_weeks_to_update, schedule_start_date
                ).run_auto_update_for_weeks()
        except Exception as e:
            logger.exception(
                "UTP failed",
                extra=log_extra_fields(
                    exception_message=str(e),
                    user_auth_id=user_id,
                    service_type=ServiceType.INTERNAL.value,
                ),
            )

        # If a new planned_day is created for current utc day, then the user will have
        # an active actual_day which points to the previously active planned_day.
        # So a new actual_day is created from that actual_day which will contain
        # the day_code of newly created planned_day
        actual_day = user.actual_days.filter(
            activity_date=schedule_start_date, is_active=True
        ).last()
        if actual_day:
            actual_day.day_code = (
                user.planned_days.filter(
                    activity_date=schedule_start_date, is_active=True
                )
                .last()
                .day_code
            )
            create_new_model_instance(actual_day)
            actual_day.reason = "UTP process for changing availability"
            actual_day.save()

    except Exception as e:
        logger.exception(
            "Failed to update training plan",
            extra=log_extra_fields(
                exception_message=str(e),
                user_auth_id=user_id,
                service_type=ServiceType.INTERNAL.value,
            ),
        )
    else:
        clear_user_cache(user)
        logger.info(
            "Successfully updated training plan.",
            extra=log_extra_fields(
                user_auth_id=user_id, service_type=ServiceType.INTERNAL.value
            ),
        )


def run_auto_update():
    try:
        start_time = datetime.datetime.now()

        autoupdate_start_datetime = get_auto_update_start_datetime()
        timezone_offset = get_timezone_offset_from_datetime_diff(
            autoupdate_start_datetime - start_time
        )
        first_cron_time_diff = time_diff_between_two_timezone_offsets(
            FIRST_TIMEZ0NE_OFFSET, timezone_offset
        )
        first_cron_start_time = start_time - datetime.timedelta(
            seconds=first_cron_time_diff
        )
        cron_code = CronHistoryLog.CronCode.AUTO_UPDATE_TRAINING_PLAN

        users = UserAuthModel.objects.filter(
            is_active=True,
            profile_data__timezone__offset=timezone_offset,
            profile_data__is_active=True,
        )
        notify_user_ids = []
        for user in users:
            try:
                if not is_user_valid_for_auto_update(
                    user, start_time, first_cron_start_time, cron_code
                ):
                    continue
                logger.info(f"Auto update training plan started for user {user.email}")
                update_user_training_plan(user.id)
                data_details = get_data_details_dict(user, "UTP is successful")
                user_activity_log = UserActivityLog(
                    user_auth=user,
                    user_id=user.code,
                    data=data_details,
                    activity_code=UserActivityLog.ActivityCode.AUTO_UPDATE_SUCCESSFUL_FOR_USER,
                )
                user_activity_log.save()
                notify_user_ids.append(user.id)
            except Exception as e:
                logger.exception(
                    "Auto update failed for single user",
                    extra=log_extra_fields(
                        user_auth_id=user.id,
                        exception_message=str(e),
                        service_type=ServiceType.CRON.value,
                    ),
                )
                continue

    except Exception as e:
        logger.exception(
            "Auto update cron failed",
            extra=log_extra_fields(
                exception_message=str(e), service_type=ServiceType.CRON.value
            ),
        )


@shared_task
def update_old_user_training_plan(user_auth_id):
    user = UserAuthModel.objects.filter(id=user_auth_id).last()
    current_date = datetime.date.today()
    user_weeks_to_update = UserWeek.objects.filter(
        user_block__user_auth=user, start_date__gt=current_date, is_active=True
    ).order_by("start_date")
    try:
        UpdateTrainingPlan(
            user, user_weeks_to_update, is_utp=False
        ).run_auto_update_for_weeks()
    except Exception as e:
        logger.exception(
            "Failed to update old user's training plan",
            extra=log_extra_fields(
                exception_message=str(e),
                user_auth_id=user.id,
                service_type=ServiceType.INTERNAL.value,
            ),
        )
