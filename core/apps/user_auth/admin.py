import json
import logging
import uuid
from datetime import date, datetime, timedelta

import requests
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

from core.apps.achievements.models import PersonalRecord

# from core.apps.achievements.utils import update_user_achievement_data
from core.apps.activities.pillar.models import Activity
from core.apps.activities.services import (
    DakghorDataTransferService,
    ReevaluationService,
)
from core.apps.block.models import UserBlock
from core.apps.challenges.models import UserChallenge
from core.apps.challenges.services import ChallengeService
from core.apps.common.common_functions import clear_user_cache
from core.apps.common.const import USER_UTP_SETTINGS_QUEUE_PRIORITIES
from core.apps.common.enums.daroan_urls_enum import DaroanURLEnum
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.models import CronHistoryLog
from core.apps.common.tp_common_tasks import recalculate_user_all_curve_data
from core.apps.common.utils import get_headers, log_extra_fields
from core.apps.daily.models import ActualDay, PlannedDay, UserDay
from core.apps.daily.services import DayMigrationService
from core.apps.evaluation.daily_evaluation.utils import day_morning_calculation
from core.apps.event.models import UserEvent
from core.apps.garmin.models import CurveCalculationData
from core.apps.garmin.utils import update_garmin_permissions
from core.apps.notification.models import (
    NotificationHistory,
    PushNotificationLog,
    PushNotificationSetting,
    UserNotificationSetting,
)
from core.apps.plan.models import UserPlan
from core.apps.session.models import ActualSession, PlannedSession, UserAway
from core.apps.session.services import MigrationService, PopulateService
from core.apps.session.tasks import (
    populate_actual_session_code_admin_task,
    populate_user_actual_intervals,
)
from core.apps.session.utils import (
    clear_current_weeks_sessions,
    update_user_actual_session_date_time_fields,
)
from core.apps.settings.models import UserSettings, UserSettingsQueue
from core.apps.user_profile.models import (
    ProfileImage,
    UserActivityLog,
    UserMetaData,
    UserPersonaliseData,
    UserProfile,
    UserTrainingAvailability,
    ZoneDifficultyLevel,
)
from core.apps.user_profile.services import (
    UserProfileService,
    ZoneDifficultyLevelService,
)
from core.apps.user_profile.utils import populate_user_access_level
from core.apps.utp.tasks import update_old_user_training_plan, update_user_training_plan
from core.apps.utp.utils import update_utp_settings
from core.apps.week.models import UserWeek

from ..common.enums.dakghor_urls_enum import DakghorURLEnum
from ..common.enums.trainer_urls import TrainerURLEnum
from ..migrate.services import (
    MigrateActualDayService,
    MigrateAthleteStateService,
    MigrateChallengeService,
    MigrateCurveCalculationData,
    MigrateDataService,
    MigratePersonalRecordService,
    MigratePillarDataService,
    MigratePlannedDayService,
    MigratePlannedSessionService,
    MigrateTrainingAvailabilityService,
    MigrateUserAwayService,
    MigrateUserBlockService,
    MigrateUserChallengeService,
    MigrateUserKnowledgeHubService,
    MigrateUserMessageService,
    MigrateUserPlanService,
    MigrateUserWeekService,
)
from ..notification.services import PushNotificationService
from ..week.services import GenerateWeekAnalysis
from .models import UserAuthModel
from .tasks import migrate_planned_data_to_trainer

logger = logging.getLogger(__name__)


def reevaluate_session(modeladmin, request, queryset):
    if "apply" not in request.POST:
        context = {
            "queryset": queryset,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "action_name": reevaluate_session.__name__,
            "title": "Run back population for following users",
            "submit_button_name": "Run Back Population",
        }
        return TemplateResponse(
            request, "admin/date_selection_form.html", context=context
        )

    start_date = datetime.strptime(request.POST["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(request.POST["end_date"], "%Y-%m-%d").date()
    for user in queryset:
        if not user.user_plans.filter().exists():
            messages.success(request, f"User has no plan. User ID: {user.id}")
            continue
        logging.info(f"Starting reevaluation service for user id: {user.id}")
        ReevaluationService.reevaluate_complete_user_data(user, start_date, end_date)
        logger.info(f"completed reevaluation service for user id: {user.id}")
        messages.success(
            request, f"Reevaluation successfully completed for User ID: {user.id}"
        )


def populate_session_planned_time_in_hr_zone_field(modeladmin, request, queryset):
    for user in queryset:
        logger.info(f"Populating planned_time_in_hr_zone for user id: {user.id}")
        PopulateService.session_planned_time_in_hr_zone_services(user)
        logger.info(f"Completed populate service for user id: {user.id}")


def clear_selected_user_cache(modeladmin, request, queryset):
    for user in queryset:
        logger.info(f"Clearing cache for user id: {user.id}")
        clear_user_cache(user)
        logger.info(f"Cleared cache for user id: {user.id}")


def auto_update_training_plan(modeladmin, request, queryset):
    for user in queryset:
        logger.info(f"Updating plan for user id: {user.id}")
        update_user_training_plan(user.id)


def reset_current_weeks_session(modeladmin, request, queryset):
    for user in queryset:
        logger.info(f"clearing current weeks sessions: {user.id}")
        clear_current_weeks_sessions(user)


def adjust_block_pss_with_week_pss(modeladmin, request, queryset):
    blocks = UserBlock.objects.filter(user_auth__in=queryset)
    for block in blocks:
        weeks_of_this_block = block.user_weeks.filter(is_active=True)
        block_pss = 0
        for week in weeks_of_this_block:
            block_pss += week.planned_pss
        block.planned_pss = block_pss
        block.save()


def run_morning_for_last_two_days(modeladmin, request, queryset):
    date_today = datetime.now().date()
    date_obj = date_today - timedelta(days=1)

    while date_obj <= date_today:
        for user in queryset:
            day_morning_calculation(user, date_obj)
        date_obj += timedelta(days=1)


def update_user_settings(modeladmin, request, queryset):
    for user in queryset:
        third_party_connect = False

        if (
            user.garmin_user_token and user.garmin_user_secret
        ) or user.strava_user_token:
            third_party_connect = True
        update_utp_settings(
            user,
            third_party_connect,
            USER_UTP_SETTINGS_QUEUE_PRIORITIES[1],
            datetime.now(),
            "admin test",
        )


def migrate_session_data_to_actual_and_planned_table(modeladmin, request, queryset):
    for user in queryset:
        logger.info(f"Session Data Migration Started: {user.id}")
        error = MigrationService.migrate_day_and_session_data(user)
        if not error:
            logger.info(f"Session Data Migration Ended Successfully: {user.id}")
        else:
            logger.info(f"Session Data Migration Failed: {user.id}")


def migrate_day_data_to_actual_and_planned_table(modeladmin, request, queryset):
    """Migrates user day data to actual and planned day table"""

    for user in queryset:
        logger.info(f"Day Data Migration Started for User ID: {user.id}")
        error = DayMigrationService.migrate_day_data(user)
        if not error:
            logger.info(
                f"Day Data Migration Ended Successfully for  User ID: {user.id}"
            )
            messages.success(request, f"Day migration done for User ID: {user.id}")
        else:
            logger.info("Day Data Migration Failed")


def populate_third_party_field_in_actual_session(modeladmin, request, queryset):
    for user in queryset:
        logger.info(f"Session Data Migration Started: {user.id}")
        MigrationService.populate_actual_session_third_party_field(user)

    messages.success(request, "Third party field populated for selected users")


def disable_auto_update(modeladmin, request, queryset):
    try:
        utp_settings = UserSettings.objects.filter(
            user__in=queryset, code="auto-update-settings-code", is_active=True
        )
        utp_settings.update(
            status=False,
            reason="admin forcefully disabled utp for this user",
            updated_by="admin",
        )
    except Exception as e:
        print(str(e))
    else:
        print("Successfully disabled UTP for the below users:")
        for user in queryset:
            print(user.email)


def enable_auto_update(modeladmin, request, queryset):
    try:
        utp_settings = UserSettings.objects.filter(
            user__in=queryset, code="auto-update-settings-code", is_active=True
        )
        utp_settings.update(
            status=True,
            reason="admin forcefully enabled utp for this user",
            updated_by="admin",
        )
    except Exception as e:
        print(str(e))
    else:
        print("Successfully enabled UTP for the below users:")
        for user in queryset:
            print(user.email)


def migrate_user_schedule_data_to_training_availability_table(
    modeladmin, request, queryset
):
    for user in queryset:
        schedule_data = user.schedule_data
        UserProfileService.migrate_user_schedule_data_to_training_availability(
            schedule_data, user
        )


def update_plan_block_week_codes(modeladmin, request, queryset):
    plans = UserPlan.objects.all()
    for plan in plans:
        plan_code = uuid.uuid4()
        plan.plan_code = plan_code
        plan.save()

        blocks = plan.user_blocks.all()
        for block in blocks:
            block_code = uuid.uuid4()
            block.block_code = block_code
            block.plan_code = plan_code
            block.save()

            weeks = block.user_weeks.all()
            for week in weeks:
                week.block_code = block_code
                week.save()


def recalculate_selected_users_curve_data(modeladmin, request, queryset):
    for user in queryset:
        recalculate_user_all_curve_data(user)
        messages.success(
            request, f"Successfully calculated curve data of User ID: {user.id}"
        )


def update_week_model_with_user_auth(modeladmin, request, queryset):
    weeks_arr = []
    weeks = UserWeek.objects.all()
    for week in weeks:
        week.user_auth = week.user_block.user_auth
        weeks_arr.append(week)
    UserWeek.objects.bulk_update(weeks, ["user_auth"])


def add_start_date_to_old_plan(modeladmin, request, queryset):
    for user in queryset:
        user_plans = UserPlan.objects.filter(user_auth=user)

        for plan in user_plans:
            plan.start_date = (
                user_plans.filter(plan_code=plan.plan_code)
                .order_by("created_at")
                .first()
                .created_at
            )
            if not plan.end_date:
                plan.end_date = plan.user_event.end_date
        UserPlan.objects.bulk_update(user_plans, ["start_date", "end_date"])


def trigger_backfill_request(modeladmin, request, queryset):
    if "apply" not in request.POST:
        context = {
            "queryset": queryset,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "action_name": trigger_backfill_request.__name__,
            "title": "Trigger Garmin backfill request for following users",
            "submit_button_name": "Trigger Backfill Request",
        }
        return TemplateResponse(
            request, "admin/date_selection_form.html", context=context
        )

    for user in queryset:
        try:
            print(
                "Backfill request start for user : "
                + str(user.id)
                + " email: "
                + user.email
            )
            url = settings.DAKGHOR_URL + "/api/v1/third-party/backfill"
            response = requests.post(
                url=url,
                json={
                    "athlete_id": user.id,
                    "start_time": request.POST["start_date"],
                    "end_time": request.POST["end_date"],
                    "source": ThirdPartySources.GARMIN.value[1].lower(),
                },
            )

            # status_code, message = get_garmin_historical_activities(user, start_time, end_time)
            if (
                response.status_code == 202
            ):  # Garmin returns status code 202 if backfill request is accepted
                messages.success(
                    request,
                    f"Successfully completed backfill request for User ID: {user.id}",
                )
            elif not response.status_code:
                messages.info(
                    request, f"No Garmin credentials found for User ID: {user.id}"
                )
            else:
                messages.error(
                    request,
                    f"Could not complete backfill request for User ID: {user.id}. "
                    f"Garmin response status code: {response.status_code}",
                )
        except Exception as e:
            messages.error(
                request,
                f"Could not complete backfill request for User ID: {user.id}. Exception: {str(e)}",
            )
            continue


# def update_achievement_data(modeladmin, request, queryset):
#     if "apply" not in request.POST:
#         context = {
#             "queryset": queryset,
#             "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
#             "action_name": update_achievement_data.__name__,
#             "title": "Update achievement data for following users",
#             "submit_button_name": "Update Achievement Data",
#         }
#         return TemplateResponse(
#             request, "admin/date_selection_form.html", context=context
#         )
#
#     start_date = datetime.strptime(request.POST["start_date"], "%Y-%m-%d").date()
#     end_date = datetime.strptime(request.POST["end_date"], "%Y-%m-%d").date()
#     # release_date = date(year=2021, month=3, day=20)  # Release date of R9
#     # if end_date < release_date:
#     #     end_date = release_date
#
#     for user in queryset:
#         try:
#             update_user_achievement_data(user, start_date, end_date)
#             messages.success(
#                 request,
#                 f"Update user achievement data successfully completed for User ID: {user.id}",
#             )
#         except Exception as e:
#             messages.error(
#                 request,
#                 f"Failed to update user achievement data for user: {user.id}. Exception: {str(e)}",
#             )


def update_challenge_data(modeladmin, request, queryset):
    for user in queryset:
        try:
            ChallengeService.update_user_challenge_data_task(user)
            messages.success(
                request,
                f"Update user challenge data successfully completed for User ID: {user.id}",
            )
        except Exception as e:
            messages.error(
                request,
                f"Failed to update user challenge data for user: {user.id}. Exception: {str(e)}",
            )


def strava_historical_activity_request(modeladmin, request, queryset):
    if "apply" not in request.POST:
        context = {
            "queryset": queryset,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "action_name": strava_historical_activity_request.__name__,
            "title": "Trigger Strava historical activity request for following users",
            "submit_button_name": "Trigger Strava Backfill Request",
        }
        return TemplateResponse(
            request, "admin/date_selection_form.html", context=context
        )

    for user in queryset:
        try:
            print(
                "Strava historical activity request start for user : "
                + str(user.id)
                + " email: "
                + user.email
            )
            url = settings.DAKGHOR_URL + "/api/v1/third-party/backfill"
            response = requests.post(
                url=url,
                json={
                    "athlete_id": user.id,
                    "start_time": request.POST["start_date"],
                    "end_time": request.POST["end_date"],
                    "source": ThirdPartySources.STRAVA.value[1].lower(),
                },
            )
            if response.status_code == 200:
                messages.success(
                    request,
                    f"Strava historical activity data successfully synced for User ID: {user.id}",
                )
            else:
                messages.warning(
                    request,
                    f"Strava historical activity dakghor process "
                    f"returned status code {response.status_code}",
                )
        except Exception as e:
            messages.error(
                request,
                f"Failed to sync Strava historical activity data for user: {user.id}. "
                f"Exception: {str(e)}",
            )


def transfer_user_info_to_dakghor(modeladmin, request, queryset):
    for user in queryset:
        try:
            DakghorDataTransferService.move_user_info_to_dakghor(user)
            messages.success(
                request, f"Successfully transferred auth data of User ID: {user.id}"
            )
        except Exception as e:
            logger.info(
                f"Dakghor auth data transfer of User: {user.id} failed. Exception: {str(e)}"
            )
            continue


def send_app_update_notification(modeladmin, request, queryset):
    if "apply" not in request.POST:
        context = {
            "queryset": queryset,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(
            request, "admin/new_app_update_form.html", context=context
        )

    request_data = request.POST

    for user in queryset:
        try:
            PushNotificationService(user).send_app_update_push_notification(
                request_data
            )
        except Exception as e:
            logger.exception(
                msg="Failed to send push notification.",
                extra=log_extra_fields(
                    exception_message=str(e),
                    user_auth_id=user.id,
                    service_type=ServiceType.ADMIN.value,
                ),
            )


send_app_update_notification.short_description = "Send App Update Notification"


# def create_push_notification_settings_for_old_user(modeladmin, request, queryset):
#     for user_auth in queryset:
#         try:
#             create_push_notification_settings(user_auth)
#             messages.success(
#                 request,
#                 f"Push notification settings creation successful for User ID: {user_auth.id}",
#             )
#         except Exception as e:
#             logger.exception(
#                 f"Failed to create notification for User ID {user_auth.id}. Exception: {str(e)}"
#             )


def populate_activity_type_in_actual_session(modeladmin, request, queryset):
    for user_auth in queryset:
        try:
            PopulateService.set_activity_type_in_actual_session(user_auth)
            messages.success(
                request,
                f"Successfully updated actual_session's activity_type for User ID: {user_auth.id}",
            )
        except Exception as e:
            logger.exception(
                f"Failed to update actual_session's activity_type for User ID {user_auth.id}. "
                f"Exception: {str(e)}"
            )


def populate_compressed_power_hr_data(modeladmin, request, queryset):
    for user_auth in queryset:
        try:
            PopulateService.set_compressed_power_hr_data(user_auth)
            messages.success(
                request,
                f"Successfully updated power hr data of User ID: {user_auth.id}",
            )
        except Exception as e:
            logger.exception(
                f"Failed to updated power hr data of User ID {user_auth.id}. "
                f"Exception: {str(e)}"
            )


def populate_actual_intervals(modeladmin, request, queryset):
    for user_auth in queryset:
        try:
            populate_user_actual_intervals.delay(user_auth.id)
            messages.success(
                request,
                f"Successfully updated actual_session's actual_intrvals for User ID: {user_auth.id}",
            )
        except Exception as e:
            logger.exception(
                f"Failed to update actual_session's actual_intrvals for User ID {user_auth.id}. "
                f"Exception: {str(e)}"
            )


def populate_actual_session_code(modeladmin, request, queryset):
    for user in queryset:
        try:
            populate_actual_session_code_admin_task(user)
            messages.success(
                request,
                f"Successfully populated actual session table's code column for user ID: {user.id}",
            )
        except Exception as e:
            logger.exception(
                f"Failed to update actual_session table code column for user ID: {user.id}. "
                f"Exception: {str(e)}"
            )
            messages.error(
                request,
                f"Failed to update actual_session table code column for user ID: {user.id}. "
                f"Exception: {str(e)}",
            )


def update_garmin_permissions_of_users(modeladmin, request, queryset):
    for user in queryset:
        try:
            response = update_garmin_permissions(user)
            if not response["error"]:
                messages.success(
                    request,
                    f"Successfully updated Garmin permission of User ID: {user.id}",
                )
                continue
            messages.error(
                request,
                f"Garmin permission update of User: {user.id} failed in Dakghor. "
                f"Exception: {response['exception']}",
            )

        except Exception as e:
            messages.error(
                request,
                f"Garmin permission update of User: {user.id} failed. Exception: {str(e)}",
            )
            continue


def update_zone_difficulty_level_for_old_user(modeladmin, request, queryset):
    for user in queryset:
        try:
            if ZoneDifficultyLevel.objects.filter(user_auth=user.id).exists():
                messages.success(
                    request,
                    f"No need to create zone difficulty level for User ID: {user.id}",
                )
                continue

            ZoneDifficultyLevelService.update_zone_difficulty_level_for_old_user(user)
            messages.success(
                request,
                f"Successfully created zone difficulty level for User ID: {user.id}",
            )
        except Exception as e:
            messages.error(
                request,
                f"Failed to create zone difficulty level for User: {user.id}. Exception: {str(e)}",
            )
            continue


def update_old_user_training_plan_for_zone_difficulty_level(
    modeladmin, request, queryset
):
    for user in queryset:
        try:
            if user.user_plans.filter(
                is_active=True, end_date__gt=date.today()
            ).exists():
                update_old_user_training_plan.delay(user.id)
                messages.success(
                    request, f"Successfully update training plan for User ID: {user.id}"
                )
            else:
                messages.success(
                    request, f"No active plan to update for User ID: {user.id}"
                )
        except Exception as e:
            messages.error(
                request,
                f"Failed to update training plan for User: {user.id}. Exception: {str(e)}",
            )
            continue


def populate_access_level(modeladmin, request, queryset):
    for user_auth in queryset:
        try:
            populate_user_access_level(user_auth)
            messages.success(
                request,
                f"Successfully updated user_profile's access_level for User ID: {user_auth.id}",
            )
        except Exception as e:
            messages.error(
                request,
                f"Failed to update user_profile's access_level for User ID {user_auth.id}. "
                f"Exception: {str(e)}",
            )


def mirgate_training_availability_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for training availability"""
                payload = MigrateTrainingAvailabilityService(
                    user_id=user.code
                ).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_TRAINING_AVAILABILITY.value

                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate training availability data for user {user.id} {response.json()}",
                )

        except Exception as e:
            messages.error(
                request,
                f"Failed to  migrate training availability data for user {user.id}",
            )
            logger.exception(
                f"Failed to update training plan for User: {user.code}. Exception: {str(e)}"
            )


def mirgate_user_plan_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the user plan"""
                payload = MigrateUserPlanService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_USER_PLAN.value
                payload = json.dumps(payload, indent=4, sort_keys=True, default=str)
                payload = json.loads(payload)
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate user plan for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(request, f"Failed to migrate user plan for user {user.id}")
            logger.exception(
                f"Failed to migrate user plan for User: {user.code}. Exception: {str(e)}"
            )


def migrate_planned_day_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the planned day"""
                payload = MigratePlannedDayService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_PLANNED_DAY.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate planned day for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(request, f"Failed to migrate planned day for user {user.id}")
            logger.exception(
                f"Failed to migrate planned day for User: {user.code}. Exception: {str(e)}"
            )


def migrate_planned_session_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the planned session"""
                payload = MigratePlannedSessionService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_PLANNED_SESSION.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate planned session for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(
                request, f"Failed to migrate planned session for user {user.id}"
            )
            logger.exception(
                f"Failed to migrate planned session for User: {user.code}. Exception: {str(e)}"
            )


def migrate_user_knowledge_hub_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                payload = MigrateUserKnowledgeHubService(
                    user_id=user.code
                ).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_USER_KNOWLEDGE_HUB.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate user knowledge hub data for user {user.id} {response.json()}",
                )

        except Exception as e:
            messages.error(
                request,
                f"Failed to migrate user knowledge hub data for user {user.id}",
            )
            logger.exception(
                f"Failed to migrate knowledge hub for User: {user.code}. Exception: {str(e)}"
            )


def migrate_personal_record_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                payload = MigratePersonalRecordService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_PERSONAL_RECORD.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate personal record data for user {user.id} {response.json()}",
                )

        except Exception as e:
            messages.error(
                request,
                f"Failed to migrate personal record data for user {user.id}",
            )
            logger.exception(
                f"Failed to migrate personal records for User: {user.code}. Exception: {str(e)}"
            )


def migrate_user_away_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                payload = MigrateUserAwayService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_USER_AWAY.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )

                messages.success(
                    request,
                    f"Successfully migrate user away data for user {user.id} {response.json()}",
                )

        except Exception as e:
            messages.error(
                request,
                f"Failed to migrate user away data for user {user.id}",
            )
            logger.exception(
                f"Failed to migrate user away data for User: {user.code}. Exception: {str(e)}"
            )


def migrate_challenge_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                payload = MigrateChallengeService(user_id=user.code).migrate_data()
                url = TrainerURLEnum.MIGRATE_CHALLENGE.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate challenge data for user {user.id} {response.json()}",
                )

        except Exception as e:
            messages.error(
                request,
                f"Failed to migrate challenge data for user {user.id}",
            )
            logger.exception(f"Failed to migrate challenge data. Exception: {str(e)}")


def migrate_user_challenge_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                payload = MigrateUserChallengeService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_USER_CHALLENGE.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate user challenge data for user {user.id} {response.json()}",
                )

        except Exception as e:
            messages.error(
                request,
                f"Failed to migrate user challenge data for user {user.id}",
            )
            logger.exception(
                f"Failed to migrate user challenge data for User: {user.code}. Exception: {str(e)}"
            )


def migrate_user_block_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the user block"""
                payload = MigrateUserBlockService(user).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_USER_BLOCK.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate user block for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(request, f"Failed to  migrate user block for user {user.id}")
            logger.exception(
                f"Failed to migrate user block for User: {user.code}. Exception: {str(e)}"
            )


def migrate_user_week_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the user week"""
                payload = MigrateUserWeekService(user).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_USER_WEEK.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrate user week for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(request, f"Failed to  migrated user week for user {user.id}")
            logger.exception(
                f"Failed to migrate user week for User: {user.code}. Exception: {str(e)}"
            )


def migrate_pillar_data_with_actual_session_and_score(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the pillar data,
                actual session and session score
                """
                payload = MigratePillarDataService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_PILLAR_DATA.value
                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrated pillar data, session score, actual session for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(
                request,
                f"Failed to  migrated pillar data, session score, actual session data for user {user.id}",
            )
            logger.exception(
                f"Failed to migrate pillar data for User: {user.code}. Exception: {str(e)}"
            )


def migrate_actual_day_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the actual day"""
                payload = MigrateActualDayService(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_ACTUAL_DAY_DATA.value

                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrated actual day data for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(
                request, f"Failed to  migrated actual day data for user {user.id}"
            )
            logger.exception(
                f"Failed to migrate actual day data for User: {user.code}. Exception: {str(e)}"
            )


def migrate_curve_calculation_data_core_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            if user.code:
                """Here generate the payload for the curve calculation data"""
                payload = MigrateCurveCalculationData(user_id=user.code).migrate_data()
                if payload is None:
                    messages.success(
                        request,
                        f"Nothing to migrate for user {user.id}",
                    )
                    continue
                url = TrainerURLEnum.MIGRATE_CURVE_CALCULATION_DATA.value

                response = MigrateDataService(user_id=user.code).send_migrate_data(
                    payload, url
                )
                messages.success(
                    request,
                    f"Successfully migrated curve calculation data for user {user.id} {response.json()}",
                )
        except Exception as e:
            messages.error(
                request,
                f"Failed to  migrated curve calculation data for user {user.id}",
            )
            logger.exception(
                f"Failed to migrate curve calculation data for User: {user.code}. Exception: {str(e)}"
            )


def migrate_user_data_to_daroan(modeladmin, request, queryset):
    try:
        users = [
            {"email": user.email, "encrypted_password": user.password}
            for user in queryset
        ]
        url = DaroanURLEnum.MIGRATE_USER.value
        response = requests.post(url=url, json=users)
        users = response.json()["data"]

        for user in users:
            UserAuthModel.objects.filter(email=user["email"]).update(code=user["code"])
        messages.success(request, "Migrated user successfully")
    except Exception as e:
        logger.exception(
            "Failed to migrate user data",
            extra=log_extra_fields(
                service_type=ServiceType.ADMIN.value, exception_message=str(e)
            ),
        )
        messages.error(request, "Migration Unsuccessful")


def populate_user_id_in_models(modeladmin, request, queryset):
    for user in queryset:
        try:
            model_classes = [
                PersonalRecord,
                Activity,
                UserBlock,
                UserChallenge,
                UserDay,
                PlannedDay,
                ActualDay,
                UserEvent,
                CurveCalculationData,
                UserNotificationSetting,
                PushNotificationSetting,
                PushNotificationLog,
                UserPlan,
                PlannedSession,
                ActualSession,
                UserAway,
                UserProfile,
                UserPersonaliseData,
                UserActivityLog,
                UserMetaData,
                ZoneDifficultyLevel,
                UserWeek,
                ProfileImage,
                UserTrainingAvailability,
                CronHistoryLog,
                UserSettings,
                UserSettingsQueue,
            ]
            for model_class in model_classes:
                model_class.objects.filter(user_auth=user, user_id__isnull=True).update(
                    user_id=user.code
                )
            NotificationHistory.objects.filter(
                receiver=user, user_id__isnull=True
            ).update(user_id=user.code)
            messages.success(request, f"Populated user code for User: {str(user.id)}")
        except Exception as e:
            msg = "Failed to populate user code"
            logger.exception(
                msg,
                extra=log_extra_fields(
                    user_auth_id=user.id,
                    exception_message=str(e),
                    service_type=ServiceType.ADMIN.value,
                ),
            )
            messages.error(request, msg + f" for {user.id}")


def run_auto_update_for_current_week(modeladmin, request, queryset):
    current_date = date.today()
    current_date = str(current_date - timedelta(current_date.weekday()))
    for user in queryset:
        try:
            if not user.code:
                messages.success(request, f"User has no code {user.id}")
                continue

            url = TrainerURLEnum.RUN_UTP.value
            headers = get_headers(user.code)
            payload = {"athlete_id": str(user.code), "start_date": current_date}
            response = requests.post(url=url, json=payload, headers=headers)

            success_msg = f"Successfully run UTP for user {user.id} {response.json()}"
            messages.success(request, success_msg)
        except Exception as e:
            messages.error(request, f"Failed to run UTP for user {user.id}")
            logger.exception(f"Failed to run UTP. Exception: {str(e)}")


def run_week_analysis_report(modeladmin, request, queryset):
    current_date = date.today()
    for user in queryset:
        try:
            GenerateWeekAnalysis(user, current_date).generate_report()
            messages.success(request, f"Successfully run for User ID: {user.id}")
        except Exception as e:
            logger.exception(str(e))
            messages.error(request, f"Failed to run for User ID {user.id}")


def update_actual_session_date_time_fields(modeladmin, request, queryset):
    for user in queryset:
        try:
            update_user_actual_session_date_time_fields(user)
            messages.success(
                request,
                f"Successfully updated session date time for User ID: {user.id}",
            )
        except Exception as e:
            logger.exception(str(e))
            messages.error(
                request, f"Failed update session date time for User ID {user.id}"
            )


def migrate_data_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            migrate_planned_data_to_trainer(user)
            messages.success(request, f"Successfully migrated data. User ID: {user.id}")
        except Exception as e:
            messages.error(request, f"Failed to migrate data. User ID: {user.id}")
            logger.exception(
                str(e),
                extra=log_extra_fields(
                    service_type=ServiceType.ADMIN.value,
                    user_id=user.code,
                    exception_message=str(e),
                ),
            )


def migrate_user_code_to_dakghor(modeladmin, request, queryset):
    codes = []
    for user in queryset:
        if user.code:
            code = {"athlete_id": user.id, "athlete_code": str(user.code)}
            codes.append(code)
    try:
        url = DakghorURLEnum.USER_CORE_MIGRATE.value
        response = requests.post(url=url, json={"codes": codes})
        messages.success(request, f"Successfully migrated data. {response.json()}")
    except Exception as e:
        messages.error(request, "Failed to migrate data")
        logger.exception(
            str(e),
            extra=log_extra_fields(
                service_type=ServiceType.ADMIN.value,
                exception_message=str(e),
            ),
        )


def migrate_joining_date_to_daroan(modeladmin, request, queryset):
    _dicts = []
    for user in queryset:
        if user.code:
            _dict = {"code": str(user.code), "joining_date": str(user.created_at)}
            _dicts.append(_dict)

    try:
        url = DaroanURLEnum.MIGRATE_JOINING_DATE.value
        response = requests.post(url=url, json={"data": _dicts})
        messages.success(request, f"Successfully migrated data. {response.json()}")
    except Exception as e:
        messages.error(request, "Failed to migrate data")
        logger.exception(
            str(e),
            extra=log_extra_fields(
                service_type=ServiceType.ADMIN.value,
                exception_message=str(e),
            ),
        )


def migrate_athlete_state_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            _data = MigrateAthleteStateService(user_id=user.code).get_request_data()
            url = TrainerURLEnum.MIGRATE_ATHLETE_STATE_DATA.value
            response = requests.post(url=url, json=_data)
            messages.success(
                request,
                f"Successfully migrate athlete state for user {user.id} {response.json()}",
            )
        except Exception as e:
            messages.error(
                request, f"Failed to migrate athlete state for user {user.id}"
            )
            logger.exception(
                str(e),
                extra=log_extra_fields(
                    service_type=ServiceType.ADMIN.value,
                    exception_message=str(e),
                ),
            )


def migrate_athlete_difficulty_state_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            _data = MigrateAthleteStateService(user_id=user.code).get_request_data()
            url = TrainerURLEnum.MIGRATE_ATHLETE_DIFFICULTY_STATE_DATA.value
            response = requests.post(url=url, json=_data)
            messages.success(
                request,
                f"Successfully migrate athlete difficulty state for user {user.id} {response.json()}",
            )
        except Exception as e:
            messages.error(
                request,
                f"Failed to migrate difficulty athlete state for user {user.id}",
            )
            logger.exception(
                str(e),
                extra=log_extra_fields(
                    service_type=ServiceType.ADMIN.value,
                    exception_message=str(e),
                ),
            )


def fix_broken_weeks(modeladmin, request, queryset):
    for user in queryset:
        url = TrainerURLEnum.FIX_BROKEN_WEEK.value
        user_profile = UserProfile.objects.filter(
            user_id=user.code, is_active=True
        ).last()
        response = requests.post(
            url=url,
            json={
                "user_id": str(user.code),
                "timezone_offset": user_profile.timezone.offset,
            },
        )
        if response.status_code == 200:
            messages.success(
                request,
                f"Successfully fixed broken weeks for user {user.id} {response.json()}",
            )
        else:
            messages.error(request, f"Failed to fix broken weeks for user {user.id}")


# required
def migrate_user_message_to_trainer(modeladmin, request, queryset):
    for user in queryset:
        try:
            _data = MigrateUserMessageService(user_id=user.code).get_request_data()
            url = TrainerURLEnum.MIGRATE_USER_MESSAGE.value
            response = requests.post(url=url, json=_data)
            messages.success(
                request,
                f"Successfully migrate user message for user {user.id} {response.json()}",
            )
        except Exception as e:
            messages.error(
                request, f"Failed to migrate user message for user {user.id}"
            )
            logger.exception(
                str(e),
                extra=log_extra_fields(
                    service_type=ServiceType.ADMIN.value,
                    exception_message=str(e),
                ),
            )


class UserAuthModelAdmin(admin.ModelAdmin):
    list_filter = ("is_active",)
    actions = [
        mirgate_training_availability_data_core_to_trainer,
        mirgate_user_plan_data_core_to_trainer,
        migrate_planned_day_data_core_to_trainer,
        migrate_planned_session_data_core_to_trainer,
        migrate_user_block_data_core_to_trainer,
        migrate_user_week_data_core_to_trainer,
        migrate_user_knowledge_hub_data_core_to_trainer,
        migrate_personal_record_data_core_to_trainer,
        migrate_user_away_data_core_to_trainer,
        migrate_challenge_data_core_to_trainer,
        migrate_user_challenge_data_core_to_trainer,
        migrate_pillar_data_with_actual_session_and_score,
        migrate_actual_day_data_core_to_trainer,
        migrate_curve_calculation_data_core_to_trainer,
        migrate_athlete_state_to_trainer,
        migrate_athlete_difficulty_state_to_trainer,
        # migrate_user_message_to_trainer,
        # reevaluate_session,
        clear_selected_user_cache,  # TODO: Refactor existing code to use this
        # auto_update_training_plan,
        # reset_current_weeks_session,
        # update_user_settings,
        # adjust_block_pss_with_week_pss,
        # disable_auto_update,
        # enable_auto_update,
        # migrate_user_schedule_data_to_training_availability_table,
        # update_plan_block_week_codes,
        # migrate_day_data_to_actual_and_planned_table,
        # recalculate_selected_users_curve_data,
        # update_week_model_with_user_auth,
        # add_start_date_to_old_plan,
        # trigger_backfill_request,
        # update_achievement_data,
        # update_challenge_data,
        # strava_historical_activity_request,
        send_app_update_notification,
        # create_push_notification_settings_for_old_user,
        # transfer_user_info_to_dakghor,
        # populate_compressed_power_hr_data,
        # populate_actual_intervals,
        # populate_actual_session_code,
        # populate_activity_type_in_actual_session,
        # update_garmin_permissions_of_users,
        # update_zone_difficulty_level_for_old_user,
        # update_old_user_training_plan_for_zone_difficulty_level,
        # populate_access_level,
        # migrate_user_data_to_daroan,
        populate_user_id_in_models,
        run_auto_update_for_current_week,
        # run_week_analysis_report,
        # update_actual_session_date_time_fields,
        # migrate_data_to_trainer,
        # migrate_user_code_to_dakghor,
        # migrate_joining_date_to_daroan,
        fix_broken_weeks,
    ]


admin.site.register(UserAuthModel, UserAuthModelAdmin)
