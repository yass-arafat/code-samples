import logging
from datetime import date, datetime, timedelta

from core.apps.common.common_functions import get_timezone_offset_from_datetime_diff
from core.apps.common.const import FIRST_TIMEZ0NE_OFFSET, WEEK_ANALYSIS_CRONJOB_TIME
from core.apps.common.date_time_utils import (
    convert_timezone_offset_to_seconds,
    time_diff_between_two_timezone_offsets,
)
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.models import CronHistoryLog
from core.apps.common.utils import log_extra_fields
from core.apps.notification.services import NotificationService, PushNotificationService
from core.apps.session.tasks import is_cron_already_done_for_user
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.models import UserActivityLog
from core.apps.week.services import GenerateWeekAnalysis

logger = logging.getLogger(__name__)


def generate_week_analysis():
    try:
        start_time = datetime.now().replace(second=0, microsecond=0)

        timezone_offset = get_timezone_offset_from_datetime_diff(
            datetime.combine(date.today(), WEEK_ANALYSIS_CRONJOB_TIME) - start_time
        )
        first_cron_time_diff = time_diff_between_two_timezone_offsets(
            FIRST_TIMEZ0NE_OFFSET, timezone_offset
        )
        first_cron_start_time = start_time - timedelta(seconds=first_cron_time_diff)

        user_local_date = (
            start_time
            + timedelta(seconds=convert_timezone_offset_to_seconds(timezone_offset))
        ).date()
        users = UserAuthModel.objects.filter(
            is_active=True,
            profile_data__timezone__offset=timezone_offset,
            profile_data__is_active=True,
        )

        cron_code = CronHistoryLog.CronCode.WEEK_ANALYSIS
        cron_logs = []
        for user in users:
            try:
                if not user.user_plans.filter(
                    end_date__gte=user_local_date, is_active=True
                ).exists():
                    continue

                if is_cron_already_done_for_user(
                    user,
                    start_time,
                    first_cron_start_time,
                    cron_code=CronHistoryLog.CronCode.WEEK_ANALYSIS,
                ):
                    continue

                week_analysis = GenerateWeekAnalysis(
                    user, user_local_date
                ).generate_report()

                UserActivityLog.objects.create(
                    user_auth=user,
                    user_id=user.code,
                    data={"week_analysis_code": str(week_analysis.code)},
                    activity_code=UserActivityLog.ActivityCode.WEEK_ANALYSIS_REPORT,
                )

                cron_status = CronHistoryLog.StatusCode.SUCCESSFUL
                NotificationService(user.code).create_week_analysis_notification(
                    week_analysis.code
                )
                PushNotificationService(user).send_week_analysis_push_notification(
                    week_analysis
                )
            except Exception as e:
                cron_status = CronHistoryLog.StatusCode.FAILED
                logger.exception(
                    "Failed to generate week analysis for user",
                    extra=log_extra_fields(
                        exception_message=str(e),
                        user_auth_id=user.id,
                        user_id=user.code,
                        service_type=ServiceType.CRON.value,
                    ),
                )
            cron_logs.append(
                CronHistoryLog(
                    cron_code=cron_code,
                    user_auth=user,
                    user_id=user.code,
                    status=cron_status,
                )
            )
    except Exception as e:
        logger.exception(
            "Failed to generate week analysis",
            extra=log_extra_fields(
                exception_message=str(e), service_type=ServiceType.CRON.value
            ),
        )
