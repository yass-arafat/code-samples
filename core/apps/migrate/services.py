import logging
from datetime import datetime

import requests

from core.apps.achievements.models import PersonalRecord
from core.apps.activities.pillar.models import Activity as PillarData
from core.apps.activities.utils import daroan_get_athlete_info
from core.apps.block.models import UserBlock
from core.apps.challenges.models import Challenge, UserChallenge
from core.apps.common.const import MIN_STARTING_LOAD, UTC_TIMEZONE
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.utils import get_headers
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.event.models import UserEvent
from core.apps.garmin.models import CurveCalculationData
from core.apps.migrate.serializers import (
    MigrateActualDaySerializer,
    MigrateActualSessionSerializer,
    MigrateChallengeSerializer,
    MigrateCurveCalculationDataSerializer,
    MigratePersonalRecordSerializer,
    MigratePillarDataSerializer,
    MigratePlannedDaySerializer,
    MigratePlannedSessionSerializer,
    MigrateSessionScoreSerializer,
    MigrateUserAwayIntervalSerializer,
    MigrateUserAwaySerializer,
    MigrateUserChallengeSerializer,
    MigrateUserKnowledgeHubSerializer,
)
from core.apps.packages.models import UserKnowledgeHub, UserPackage
from core.apps.plan.models import UserPlan
from core.apps.session.models import (
    ActualSession,
    PlannedSession,
    SessionScore,
    UserAway,
    UserAwayInterval,
)
from core.apps.user_profile.models import (
    UserPersonaliseData,
    UserProfile,
    UserTrainingAvailability,
    ZoneDifficultyLevel,
)
from core.apps.user_profile.services import UserProfileService
from core.apps.week.models import UserWeek

logger = logging.getLogger(__name__)


class MigratePillarDataService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]

    def _get_pillar_data(self):
        return PillarData.objects.filter(user_id=self.user_id).all()

    def _get_actual_session_data(self):
        return ActualSession.objects.filter(
            user_id=self.user_id, third_party__isnull=False, is_active=True
        ).all()

    def _get_session_score_data(self):
        return SessionScore.objects.filter(user_id=self.user_id).all()

    def _get_session_score_data_by_id_list(self, id_list):
        return SessionScore.objects.filter(pk__in=id_list).all()

    def migrate_data(self):
        if not ActualSession.objects.filter(
            user_id=self.user_id, third_party__isnull=False, is_active=True
        ).exists():
            return
        actual_session_data = self._get_actual_session_data()

        # pillar_data_id_list = list(map(lambda d: d.pillar_data_id, actual_session_data))
        session_score_id_list = list(
            map(lambda d: d.session_score_id, actual_session_data)
        )

        return {
            "pillar_data": MigratePillarDataSerializer(
                self._get_pillar_data(), many=True
            ).data,
            "actual_session": MigrateActualSessionSerializer(
                actual_session_data, many=True
            ).data,
            "session_score": MigrateSessionScoreSerializer(
                self._get_session_score_data_by_id_list(session_score_id_list),
                many=True,
            ).data,
        }


class MigrateUserPlanService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.user_plans = self._get_user_plans()

    def _get_user_event(self, user_event_id):
        return UserEvent.objects.filter(user_id=self.user_id, id=user_event_id).values()

    def _get_user_package(self, user_package_id):
        return UserPackage.objects.filter(
            user_id=self.user_id, id=user_package_id
        ).values()

    def _get_user_plans(self):
        return UserPlan.objects.filter(user_id=self.user_id, is_active=True).values()

    def _get_total_days_in_plan(self, plan_code):
        return (
            UserPlan.objects.filter(user_id=self.user_id, plan_code=plan_code)
            .order_by("created_at")
            .first()
            .total_days_in_plan
        )

    def _get_starting_prs(self):
        return (
            UserPersonaliseData.objects.filter(user_id=self.user_id, is_active=True)
            .last()
            .starting_prs
        )

    def _get_user_date_of_birth(self):
        user_date_of_birth = (
            UserPersonaliseData.objects.filter(user_id=self.user_id, is_active=True)
            .last()
            .date_of_birth
        )
        user_date_of_birth = str(user_date_of_birth)
        return user_date_of_birth

    def migrate_data(self):
        if not self.user_plans:
            return

        plans = []
        for user_plan in self.user_plans:
            user_package = None
            user_event = None
            user_plan["starting_prs"] = self._get_starting_prs()
            if user_plan["user_event_id"]:
                user_event = self._get_user_event(user_plan["user_event_id"])
            if user_plan["user_package_id"]:
                user_package = self._get_user_package(user_plan["user_package_id"])
                user_plan["total_days_in_plan"] = self._get_total_days_in_plan(
                    user_plan["plan_code"]
                )

            data = {
                "user_plan": user_plan,
                "user_package": user_package[0] if user_package else None,
                "user_event": user_event[0] if user_event else None,
            }
            plans.append(data)

        extra = {
            "date_of_birth": self._get_user_date_of_birth(),
        }

        migrate_data = {
            "plans": plans,
            "extra": extra,
        }
        return migrate_data


class MigrateTrainingAvailabilityService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.user_training_availability = self._get_user_training_availability()

    def _get_user_training_availability(self):
        # user_training_availability --> table
        return (
            UserTrainingAvailability.objects.filter(
                user_id=self.user_id,
            )
            .select_related(
                "days_commute_by_bike",
                "available_training_hours_per_day_outside_commuting",
            )
            .last()
        )

    def _get_commute_durations(self):
        duration = (
            self.user_training_availability.duration_single_commute_in_hours * 3600
        )
        commute_durations = []

        # commute_by_bike_day --> table
        days_commute_by_bike = self.user_training_availability.days_commute_by_bike

        if self.user_training_availability.commute_to_work_by_bike:
            if days_commute_by_bike.first_day:
                commute_durations.append(int(duration))
            else:
                commute_durations.append(0)
            if days_commute_by_bike.second_day:
                commute_durations.append(int(duration))
            else:
                commute_durations.append(0)
            if days_commute_by_bike.third_day:
                commute_durations.append(int(duration))
            else:
                commute_durations.append(0)
            if days_commute_by_bike.fourth_day:
                commute_durations.append(int(duration))
            else:
                commute_durations.append(0)
            if days_commute_by_bike.fifth_day:
                commute_durations.append(int(duration))
            else:
                commute_durations.append(0)
            if days_commute_by_bike.sixth_day:
                commute_durations.append(int(duration))
            else:
                commute_durations.append(0)
            if days_commute_by_bike.seventh_day:
                commute_durations.append(int(duration))
            else:
                commute_durations.append(0)

        return commute_durations

    def _get_available_durations(self):
        # training_duration --> table
        training_duration = (
            self.user_training_availability.available_training_hours_per_day_outside_commuting
        )

        return [
            int(training_duration.first_day_duration * 3600),
            int(training_duration.second_day_duration * 3600),
            int(training_duration.third_day_duration * 3600),
            int(training_duration.fourth_day_duration * 3600),
            int(training_duration.fifth_day_duration * 3600),
            int(training_duration.sixth_day_duration * 3600),
            int(training_duration.seventh_day_duration * 3600),
        ]

    def migrate_data(self):
        if not self.user_training_availability:
            return
        commute_durations = self._get_commute_durations()
        available_durations = self._get_available_durations()
        is_commuting = self.user_training_availability.commute_to_work_by_bike
        return {
            "is_commuting": is_commuting,
            "commute_durations": commute_durations,
            "available_durations": available_durations,
        }


class MigratePlannedSessionService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.planned_sessions = self._get_planned_sessions()

    def _get_planned_sessions(self):
        planned_sessions_obj = PlannedSession.objects.filter(
            user_id=self.user_id, is_active=True
        )

        planned_sessions = MigratePlannedSessionSerializer(
            planned_sessions_obj, many=True
        ).data
        return planned_sessions

    def migrate_data(self):
        if not PlannedSession.objects.filter(
            user_id=self.user_id, is_active=True
        ).exists():
            return
        return {"planned_sessions": self.planned_sessions}


class MigrateUserKnowledgeHubService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.user_knowledge_hub_data = self._get_user_knowledge_hub_data()

    def _get_user_knowledge_hub_data(self):
        user_knowledge_hub_data = UserKnowledgeHub.objects.filter(
            user_id=self.user_id, is_active=True
        )

        serialized_data = MigrateUserKnowledgeHubSerializer(
            user_knowledge_hub_data, many=True
        ).data
        return serialized_data

    def migrate_data(self):
        if not UserKnowledgeHub.objects.filter(
            user_id=self.user_id, is_active=True
        ).exists():
            return
        return {"user_knowledge_hub_data": self.user_knowledge_hub_data}


class MigratePersonalRecordService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.personal_records = self._get_personal_record_data()

    def _get_personal_record_data(self):
        personal_record_data = PersonalRecord.objects.filter(
            user_id=self.user_id, is_active=True
        )

        serialized_data = MigratePersonalRecordSerializer(
            personal_record_data, many=True
        ).data
        return serialized_data

    def migrate_data(self):
        if not PersonalRecord.objects.filter(
            user_id=self.user_id, is_active=True
        ).exists():
            return
        return {"personal_records": self.personal_records}


class MigrateChallengeService:
    def __init__(self, **kwargs):
        self.challenges = self._get_challenge_data()

    def _get_challenge_data(self):
        challenge_data = Challenge.objects.filter(is_active=True)

        serialized_data = MigrateChallengeSerializer(challenge_data, many=True).data
        return serialized_data

    def migrate_data(self):
        return {"challenges": self.challenges}


class MigrateUserChallengeService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.user_challenges = self._get_user_challenge_data()

    def _get_user_challenge_data(self):
        user_challenge_data = UserChallenge.objects.filter(
            user_id=self.user_id, is_active=True
        )

        serialized_data = MigrateUserChallengeSerializer(
            user_challenge_data, many=True
        ).data
        return serialized_data

    def migrate_data(self):
        if not UserChallenge.objects.filter(
            user_id=self.user_id, is_active=True
        ).exists():
            return
        return {"user_challenges": self.user_challenges}


class MigrateUserAwayService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.user_away = self._get_user_away_data()
        self.user_away_interval = self._get_user_away_interval_data()

    def _get_user_away_data(self):
        self.user_away_data = UserAway.objects.filter(
            user_id=self.user_id, is_active=True
        )
        serialized_data = MigrateUserAwaySerializer(self.user_away_data, many=True).data
        return serialized_data

    def _get_user_away_interval_data(self):
        interval_codes = list(
            self.user_away_data.values_list("interval_code", flat=True)
        )
        user_away_interval_data = UserAwayInterval.objects.filter(
            interval_code__in=interval_codes, is_active=True
        )
        serialized_data = MigrateUserAwayIntervalSerializer(
            user_away_interval_data, many=True
        ).data
        return serialized_data

    def migrate_data(self):
        if not UserAway.objects.filter(user_id=self.user_id, is_active=True).exists():
            return
        return {
            "user_away": self.user_away,
            "user_away_intervals": self.user_away_interval,
        }


class MigratePlannedDayService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]
        self.planned_days = self._get_planned_days()

    def _get_planned_days(self):
        planned_days_obj = PlannedDay.objects.filter(
            user_id=self.user_id, is_active=True
        ).values()
        planned_days = MigratePlannedDaySerializer(planned_days_obj, many=True).data
        return planned_days

    def migrate_data(self):
        if not PlannedDay.objects.filter(user_id=self.user_id, is_active=True).exists():
            return
        return {"planned_days": self.planned_days}


class MigrateUserBlockService:
    def __init__(self, user_auth):
        self.user_auth = user_auth

        self.user_plans = {}
        self._set_user_plans()

    def _get_user_blocks(self):
        return UserBlock.objects.filter(
            user_auth=self.user_auth, is_active=True
        ).order_by("start_date")

    def _set_user_plans(self):
        user_plans = (
            UserPlan.objects.filter(user_auth=self.user_auth, is_active=True)
            .order_by("start_date")
            .select_related("user_event", "user_package")
        )

        for user_plan in user_plans:
            self.user_plans[user_plan.plan_code] = {
                "user_plan": user_plan,
                "block_no": 1,
            }

    def migrate_data(self):
        if not UserBlock.objects.filter(
            user_auth=self.user_auth, is_active=True
        ).exists():
            return
        user_blocks = self._get_user_blocks()

        block_dicts = []
        for user_block in user_blocks:
            block_dict = {}
            plan_code = user_block.plan_code

            user_plan = self.user_plans[plan_code]["user_plan"]
            if user_plan.user_event_id:
                block_dict["plan_type"] = "event"
                block_dict["plan_start_date"] = str(user_plan.start_date)
                block_dict["plan_duration"] = user_plan.total_days_in_plan
            else:
                block_dict["plan_type"] = "package"
                sub_package_id = user_plan.user_package.sub_package_id
                if 1 <= sub_package_id <= 3:
                    block_dict["plan_id"] = sub_package_id + 6
                else:
                    original_plan = (
                        UserPlan.objects.filter(plan_code=user_plan.plan_code)
                        .order_by("created_at")
                        .first()
                    )
                    block_dict["plan_duration"] = original_plan.total_days_in_plan
                block_dict["sub_package_id"] = sub_package_id

            block_dict.update(
                {
                    "zone_focus": user_block.zone_focus,
                    "block_no": self.user_plans[plan_code]["block_no"],
                    "block_code": str(user_block.block_code),
                    "plan_code": str(user_block.plan_code),
                    "start_date": str(user_block.start_date),
                    "end_date": str(user_block.end_date),
                    "is_active": user_block.is_active,
                    "user_id": str(self.user_auth.code),
                }
            )
            self.user_plans[plan_code]["block_no"] += 1

            block_dicts.append(block_dict)

        data = {"user_blocks": block_dicts}
        data.update(self._get_extra_data())
        return data

    def _get_extra_data(self):
        user_personalise_data = UserPersonaliseData.objects.filter(
            user_id=self.user_auth.code,
            is_active=True,
        ).last()
        return {
            "date_of_birth": str(user_personalise_data.date_of_birth),
        }


class MigrateUserWeekService:
    def __init__(self, user_auth):
        self.user_auth = user_auth

        self.user_blocks = {}
        self._set_user_blocks()

    def _get_user_weeks(self):
        user_weeks = UserWeek.objects.filter(
            user_auth=self.user_auth, is_active=True
        ).order_by("start_date")

        week_dicts = []
        for user_week in user_weeks:
            week_dict = {
                "user_id": str(self.user_auth.code),
                "week_no": self.user_blocks[user_week.block_code]["week_no"],
                "week_code": str(user_week.week_code),
                "block_code": str(user_week.block_code),
                "start_date": str(user_week.start_date),
                "end_date": str(user_week.end_date),
                "zone_focus": user_week.zone_focus,
                "is_active": user_week.is_active,
            }
            self.user_blocks[user_week.block_code]["week_no"] += 1

            week_dicts.append(week_dict)

        return week_dicts

    def _set_user_blocks(self):
        user_blocks = UserBlock.objects.filter(
            user_auth=self.user_auth, is_active=True
        ).order_by("start_date")

        for user_block in user_blocks:
            self.user_blocks[user_block.block_code] = {
                "user_block": user_block,
                "week_no": 1,
            }

    def migrate_data(self):
        if not UserWeek.objects.filter(
            user_auth=self.user_auth, is_active=True
        ).exists():
            return
        return {"user_weeks": self._get_user_weeks()}


class MigrateDataService:
    def __init__(self, **kwargs):
        self.user_id = kwargs["user_id"]

    def send_migrate_data(self, payload, url):
        headers = get_headers(self.user_id)
        return requests.post(url=url, json=payload, headers=headers)


class MigrateAthleteStateService:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.timezone_offset = self._get_timezone_offset()
        self.user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            self.timezone_offset, datetime.now()
        )

    def _get_timezone_offset(self):
        user_profile = UserProfile.objects.filter(
            user_id=self.user_id, is_active=True
        ).last()
        if user_profile:
            return user_profile.timezone.offset
        return UTC_TIMEZONE

    def get_request_data(self):
        joining_date = self.get_joining_date()
        last_planned_date = self.get_last_planned_date()
        user_personalise_data = UserPersonaliseData.objects.filter(
            user_id=self.user_id,
            is_active=True,
            starting_acute_load__isnull=False,
            starting_load__isnull=False,
        ).first()
        if user_personalise_data:
            starting_load = max(user_personalise_data.starting_load, MIN_STARTING_LOAD)
            starting_acute_load = max(
                user_personalise_data.starting_acute_load, MIN_STARTING_LOAD
            )
        else:
            starting_load, starting_acute_load = MIN_STARTING_LOAD, MIN_STARTING_LOAD

        history_input_date = UserProfileService(
            user_id=self.user_id
        ).get_first_history_input_date()

        zone_difficulty_levels = ZoneDifficultyLevel.objects.filter(
            user_id=self.user_id, is_active=True
        ).last()

        return {
            "user_id": str(self.user_id),
            "joining_date": joining_date,
            "user_local_date": str(self.user_local_date),
            "last_planned_date": str(last_planned_date),
            "starting_load": starting_load,
            "starting_acute_load": starting_acute_load,
            "history_input_date": history_input_date,
            "difficulty_levels": {
                "DURATION": {"start_level": 0},
                "3K": {
                    "start_level": zone_difficulty_levels.zone_three_level
                    if zone_difficulty_levels
                    else 0
                },
                "4K": {
                    "start_level": zone_difficulty_levels.zone_four_level
                    if zone_difficulty_levels
                    else 0
                },
                "5K": {
                    "start_level": zone_difficulty_levels.zone_five_level
                    if zone_difficulty_levels
                    else 0
                },
                "6K": {
                    "start_level": zone_difficulty_levels.zone_six_level
                    if zone_difficulty_levels
                    else 0
                },
                "7K": {
                    "start_level": zone_difficulty_levels.zone_seven_level
                    if zone_difficulty_levels
                    else 0
                },
                "HC": {
                    "start_level": zone_difficulty_levels.zone_hc_level
                    if zone_difficulty_levels
                    else 0
                },
            },
        }

    def get_joining_date(self):
        return daroan_get_athlete_info(self.user_id)["data"]["joining_date"]

    def get_last_planned_date(self):
        last_plan = UserPlan.objects.filter(user_id=self.user_id, is_active=True).last()
        if not last_plan:
            return self.user_local_date
        return max(self.user_local_date, last_plan.end_date)


class MigrateUserMessageService:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")

    def get_request_data(self):
        user_profile = UserProfile.objects.filter(
            user_id=self.user_id, is_active=True
        ).last()
        if user_profile:
            timezone_offset = user_profile.timezone.offset
        else:
            timezone_offset = UTC_TIMEZONE
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            timezone_offset, datetime.now()
        )
        full_name = user_profile.name

        return {
            "user_id": str(self.user_id),
            "user_local_date": str(user_local_date),
            "full_name": full_name,
        }


class MigrateActualDayService:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")

    def _get_actual_day_data(self):
        return ActualDay.objects.filter(user_id=self.user_id, is_active=True).all()

    def migrate_data(self):
        if ActualDay.objects.filter(user_id=self.user_id, is_active=True).exists():
            return
        return {
            "actual_day": MigrateActualDaySerializer(
                self._get_actual_day_data(), many=True
            ).data
        }


class MigrateCurveCalculationData:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")

    def _get_curve_calculation_data(self):
        return CurveCalculationData.objects.filter(user_id=self.user_id).all()

    def migrate_data(self):
        if not CurveCalculationData.objects.filter(user_id=self.user_id).exists():
            return
        return {
            "curve_calculation": MigrateCurveCalculationDataSerializer(
                self._get_curve_calculation_data(), many=True
            ).data
        }
