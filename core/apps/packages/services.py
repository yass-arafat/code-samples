import logging
import math
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction

from core.apps.block.models import UserBlock
from core.apps.calculations.onboarding.ramp_rate_calculations import (
    get_calculated_ramp_rate,
)
from core.apps.common.common_functions import (
    clear_user_cache,
    get_auto_update_start_date,
)
from core.apps.common.const import (
    BUILD_WEEK_RAMP_RATE,
    BUILD_WEEK_TYPE,
    MAX_TYPICAL_INTENSITY,
    MIN_AVAILABLE_TRAINING_HOUR,
    MIN_STARTING_LOAD,
    MIN_WEEKLY_PSS,
    PSS_SL_MIN,
    RECOVERY_WEEK_RAMP_RATE,
    RECOVERY_WEEK_TYPE,
)
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.common.enums.service_enum import ServiceType
from core.apps.common.messages import (
    KNOWLEDGE_HUB_APP_BAR_TITLE,
    PACKAGE_DURATION_PAGE_CAPTION,
)
from core.apps.common.utils import (
    create_new_model_instance,
    log_extra_fields,
    update_is_active_value,
)
from core.apps.ctp.calculations import (
    PssCalculation,
    calculate_target_load,
    create_session_for_day,
    final_load_calculation_for_day,
    get_commute_pss_for_week,
    get_minimum_pss,
    get_number_of_sessions_of_this_type_in_this_week,
    get_number_of_week_days,
    get_session_types_for_this_week,
    get_yesterdays_session_intensity,
    is_pad_applicable,
    select_session,
)
from core.apps.ctp.services import TrainingAvailability, ZoneDifficultyService
from core.apps.daily.models import ActualDay, PlannedDay
from core.apps.plan.models import UserPlan
from core.apps.session.cached_truth_tables_utils import (
    get_rest_session,
    get_session_rule_by_session_type,
    get_session_type_by_session,
)
from core.apps.session.models import PlannedSession
from core.apps.user_auth.models import UserAuthModel
from core.apps.user_profile.models import UserPersonaliseData, ZoneDifficultyLevel
from core.apps.week.models import UserWeek

from .api.base.serializers import SubPackageSerializer
from .enums import (
    GoalTypeEnum,
    HillClimbPackageWeekRules,
    PackageDuration,
    PackageWeekRules,
)
from .models import KnowledgeHub, Package, SubPackage, UserPackage

logger = logging.getLogger(__name__)


class SubPackageService:
    @staticmethod
    def get_sub_packages(package_id):
        sub_package_objects = SubPackage.objects.filter(
            is_active=True, package_id=package_id
        ).order_by("id")
        serializer = SubPackageSerializer(sub_package_objects, many=True)
        sub_packages = serializer.data
        package = Package.objects.filter(id=package_id, is_active=True).last()

        return {"caption": package.caption, "sub_packages": sub_packages}


class BaseCreatePackagePlan:
    def __init__(self, user_package: UserPackage):
        self.user_package = user_package
        self.sub_package = self.user_package.sub_package
        self.user_id = user_package.user_id
        self.user_auth = UserAuthModel.objects.get(code=self.user_id)

        self.user_personalise_data = UserPersonaliseData.objects.filter(
            user_id=self.user_id, is_active=True
        ).last()

        self.training_availability = TrainingAvailability(self.user_auth)
        self.zone_difficulty_service = ZoneDifficultyService(
            self.user_auth, self.user_personalise_data
        )

        self.user_plan = self._create_plan()

        self.BUILD_WEEK_RAMP_RATE = None  # Must be defined by child class
        self.RECOVERY_WEEK_RAMP_RATE = None  # Must be defined by child class
        self.TOTAL_WEEKS_PER_BLOCK = None  # Must be defined by child class

        self.week_zone_focuses = self._get_week_zone_focuses()

        self.BLOCKS = []
        self.WEEKS = []
        self.DAYS = []
        self.SESSIONS = []

        self.BLOCK_NO = 0
        self.WEEK_NO = 0
        self.DAY_NO = 0

        self.current_week_allowable_pss = 0

    def _get_week_zone_focuses(self):
        return eval(self.sub_package.week_zone_focuses)

    def _create_plan(self):
        plan_start_date = self._get_plan_start_date()
        plan_end_date = self._get_plan_end_date(plan_start_date)
        return UserPlan.objects.create(
            user_id=self.user_id,
            user_auth=self.user_auth,
            user_package=self.user_package,
            start_date=plan_start_date,
            end_date=plan_end_date,
            plan_code=uuid.uuid4(),
        )

    def _get_plan_start_date(self):
        return DateTimeUtils.get_user_local_date_from_utc(
            self.user_auth.timezone_offset, datetime.now()
        )

    def _get_plan_end_date(self, plan_start_date):
        return plan_start_date + timedelta(self.sub_package.duration)

    def create_package_training_plan(self):
        self._create_blocks()
        self._store_data_in_db()

    def _create_blocks(self):
        total_blocks = self._get_total_blocks()
        block_start_date = self.user_plan.start_date
        for _ in range(total_blocks):
            self.BLOCK_NO += 1
            self._create_block(block_start_date=block_start_date)
            block_start_date += timedelta(weeks=self.TOTAL_WEEKS_PER_BLOCK)

    def _get_total_blocks(self):
        number_of_weeks = self.user_plan.total_days_in_plan / 7
        return math.ceil(number_of_weeks / self.TOTAL_WEEKS_PER_BLOCK)

    def _create_block(self, block_start_date: date):
        user_block = UserBlock(
            user_plan=self.user_plan,
            plan_code=self.user_plan.plan_code,
            number=self.BLOCK_NO,
            block_code=uuid.uuid4(),
            no_of_weeks=self.TOTAL_WEEKS_PER_BLOCK,
            start_date=block_start_date,
            end_date=self._get_block_end_date(block_start_date),
            user_id=self.user_id,
            user_auth=self.user_auth,
            planned_pss=Decimal(0.0),
        )

        self._create_weeks(user_block)
        self.BLOCKS.append(user_block)

    def _get_block_end_date(self, block_start_date):
        return block_start_date + timedelta(days=self.TOTAL_WEEKS_PER_BLOCK * 7)

    def _create_weeks(self, user_block: UserBlock):
        week_start_date = user_block.start_date  # First week's start date
        weeks_remaining = self.TOTAL_WEEKS_PER_BLOCK

        while weeks_remaining > 0:
            week = self._create_week(
                user_block,
                week_start_date,
                weeks_remaining,
            )

            week_start_date += timedelta(days=7)
            weeks_remaining -= 1

            user_block.planned_pss += Decimal(week.planned_pss)

    def _create_week(self, user_block, week_start_date, weeks_remaining):
        week_type = self._get_week_type(weeks_remaining)
        week = UserWeek(
            start_date=week_start_date,
            end_date=week_start_date + timedelta(days=6),
            user_auth=self.user_auth,
            user_block=user_block,
            week_type=week_type,
            user_id=self.user_id,
            zone_focus=self._get_week_focus(),
            week_code=uuid.uuid4(),
            block_code=user_block.block_code,
            sunday_max_load=self._get_sunday_max_load(week_type),
            commute_pss_week=get_commute_pss_for_week(self.training_availability),
        )

        # create days of this week
        self._create_week_days(week)

        # According to the 2.15 section of CTP algorithm,
        # instead of the max load like we did before.
        # As week.sunday_max_load is passed as the previous sunday load value,
        # we assign the calculated planned load value to week.sunday_max_load
        week.sunday_max_load = self.DAYS[-1].planned_load

        self.WEEKS.append(week)
        self.WEEK_NO += 1

        return week

    @staticmethod
    def _get_week_type(weeks_remaining: int) -> str:
        if weeks_remaining == 1:  # Last week of the block
            return RECOVERY_WEEK_TYPE
        return BUILD_WEEK_TYPE

    def _get_week_focus(self):
        if self.week_zone_focuses[self.WEEK_NO] == "HC":
            return 6
        return self.week_zone_focuses[self.WEEK_NO]

    def _get_sunday_max_load(self, week_type: str) -> Decimal:
        load = self._get_last_sunday_load()
        ramp_rate = self._get_week_ramp_rate(week_type)
        return load + Decimal.from_float(ramp_rate)

    def _get_last_sunday_load(self) -> Decimal:
        if self._is_starting_week():
            return self.user_personalise_data.starting_load
        return self.WEEKS[-1].sunday_max_load

    def _is_starting_week(self) -> bool:
        return bool(self.BLOCK_NO == 1)

    def _get_week_ramp_rate(self, week_type: str):
        if week_type == RECOVERY_WEEK_TYPE:
            return self.RECOVERY_WEEK_RAMP_RATE
        return self.BUILD_WEEK_RAMP_RATE

    def _create_week_days(self, week: UserWeek) -> None:
        target_load = week.sunday_max_load

        week_days = []
        activity_date = week.end_date
        while activity_date >= week.start_date:
            day = PlannedDay(
                user_auth=self.user_auth,
                activity_date=activity_date,
                max_load=target_load,
                week_code=week.week_code,
                day_code=uuid.uuid4(),
                user_id=self.user_auth.code,
            )

            target_load = calculate_target_load(day.max_load)
            week_days.append(day)
            activity_date -= timedelta(1)

        self._select_sessions_for_week_days(week, week_days[::-1])

    def _select_sessions_for_week_days(self, week, days):
        week_days = []
        selected_sessions = []
        self.current_week_allowable_pss = MIN_WEEKLY_PSS

        for day in days:
            if day.activity_date < self.user_plan.start_date:
                continue

            yesterday = self._get_yesterday(day)
            day.yesterday = yesterday
            pss_calc = PssCalculation(self.user_personalise_data, week)

            self._day_pss_calculation(day, pss_calc)

            available_training_hour = (
                self.training_availability.get_available_training_hour_for_day(
                    day.activity_date
                )
            )

            if self._check_rest_day(day, available_training_hour):
                day, session = self._set_as_rest_day(day)
            else:
                day, session = self._select_build_session(
                    week,
                    week_days,
                    day,
                    pss_calc,
                    available_training_hour,
                )

            self.DAY_NO += 1
            selected_sessions.append(session)

            week.planned_pss = Decimal(week.planned_pss) + session.planned_pss
            day.selected_session = session
            week_days.append(day)

            # Need to append it inside the loop for _get_yesterday
            self.DAYS.append(day)

            self.current_week_allowable_pss -= float(session.planned_pss)

        self.SESSIONS += selected_sessions

    def _day_pss_calculation(self, day, pss_calc):
        # commute pss calculation 2.1
        day.commute_pss_day = pss_calc.get_commute_pss_of_day(
            day, self.training_availability.commute_days
        )

        # load and acute load calculation 2.4
        (
            load_post_commute_nth_day,
            acute_load_post_commute_nth_day,
        ) = pss_calc.get_load_and_acute_load_post_commute_nth_day(day)
        day.load_post_commute = load_post_commute_nth_day
        day.acute_load_post_commute = acute_load_post_commute_nth_day

        # training pss load calculations 2.5
        day.training_pss_by_load = pss_calc.get_training_pss_load(day)

        # training pss freshness calculations 2.6
        day.training_pss_by_freshness = pss_calc.get_training_pss_freshness(day)

        # training pss max ride calculations 2.7
        day.training_pss_by_max_ride = pss_calc.get_training_pss_max_ride(day)

    def _get_yesterday(self, day):
        if len(self.DAYS):
            return self.DAYS[-1]

        day_yesterday = PlannedDay.objects.filter(
            user_auth=self.user_auth,
            activity_date=day.activity_date - timedelta(days=1),
            is_active=True,
        ).last()
        if day_yesterday:
            day_yesterday.selected_session = PlannedSession.objects.filter(
                user_auth=self.user_auth,
                session_date_time=day_yesterday.activity_date,
                is_active=True,
            ).last()
        return day_yesterday

    def _check_rest_day(self, day, available_training_hour):
        return (
            self._user_had_session_for_last_three_days()
            or available_training_hour < MIN_AVAILABLE_TRAINING_HOUR
            or self._check_pss_for_build_session(day)
        )

    def _check_pss_for_build_session(self, day) -> bool:
        return self._get_available_pss_for_build_session(day) < PSS_SL_MIN

    def _get_available_pss_for_build_session(self, day):
        return max(get_minimum_pss(day), self.current_week_allowable_pss)

    def _user_had_session_for_last_three_days(self):
        if len(self.DAYS) < 3:
            return False

        d1_session = self.DAYS[-1].selected_session
        d2_session = self.DAYS[-2].selected_session
        d3_session = self.DAYS[-3].selected_session

        session_type_codes = [
            d1_session.session_type.code,
            d2_session.session_type.code,
            d3_session.session_type.code,
        ]
        return not bool("REST" in session_type_codes)

    def _set_as_rest_day(self, day):
        rest_session = get_rest_session()
        session_type = get_session_type_by_session(rest_session)
        session = create_session_for_day(
            rest_session, session_type, day, None, padding=False
        )
        day = final_load_calculation_for_day(
            self.user_plan, day, session, None, self.user_personalise_data
        )
        day.zone_focus = session.session_type.target_zone
        session.session = rest_session
        day.selected_session = session
        return day, session

    def _select_build_session(
        self, week, week_days, day, pss_calc, available_training_hour
    ):
        session_types = self._get_session_types_for_this_week(week)
        session = None
        for session_type in session_types:
            if not self._is_valid_session_type(session_type, day, week_days, week):
                continue

            # training pss hours available calculations 2.10
            day.training_pss_by_hours = pss_calc.get_training_pss_available_hours(
                session_type,
                day,
                self.training_availability.user_available_hours,
            )

            # training pss final values calculations 2.11
            day.training_pss_final_value = self._get_available_pss_for_day(day)

            selected_session = select_session(
                day, session_type, self.zone_difficulty_service
            )
            self.zone_difficulty_service.update_zone_difficulty_level(selected_session)

            if selected_session:
                padding = self._is_pad_applicable(week, day, selected_session)

                day.zone_focus = selected_session.session_type.target_zone
                session = create_session_for_day(
                    selected_session=selected_session,
                    session_type=session_type,
                    day=day,
                    available_training_hour=available_training_hour,
                    padding=padding,
                )
                session.session = selected_session
                day = final_load_calculation_for_day(
                    self.user_plan,
                    day,
                    session,
                    None,
                    self.user_personalise_data,
                    utp=False,
                )
                break
        return day, session

    def _is_valid_session_type(self, session_type, day, week_days, week):
        session_rule = get_session_rule_by_session_type(session_type)
        if (
            (
                session_rule.typical_intensity > MAX_TYPICAL_INTENSITY
                and get_yesterdays_session_intensity(day, utp=False)
                > MAX_TYPICAL_INTENSITY
            )
            or (
                get_number_of_sessions_of_this_type_in_this_week(
                    week_days, session_type
                )
                >= session_rule.max_num_of_selected_session_type_per_week
            )
            or self._check_recovery_week_intensive_session(
                week, session_type, day, week_days
            )
        ):
            return False
        return True

    def _check_recovery_week_intensive_session(
        self, week, session_type, day, week_days
    ):
        return bool(
            week.zone_focus == 0
            and session_type.target_zone not in (0, 1)
            and (
                day.activity_date.weekday() in (0, 1)  # Monday, Tuesday
                or not self._is_build_session_assigned_this_week(week_days)
            )
        )

    @staticmethod
    def _is_build_session_assigned_this_week(week_days):
        for day in week_days:
            if day.selected_session.zone_focus != 0:
                return True
        return False

    def _get_available_pss_for_day(self, day):
        return min(
            self._get_available_pss_for_build_session(day), day.training_pss_by_hours
        )

    @staticmethod
    def _is_pad_applicable(week, day, selected_session):
        if week.zone_focus == 0:
            return False
        return is_pad_applicable(day, selected_session)

    def _get_session_types_for_this_week(self, week):
        week_zone_focus = week.zone_focus
        session_types = PackageWeekRules.get_session_types(week_zone_focus)
        return session_types

    def _store_data_in_db(self):
        UserBlock.objects.bulk_create(self.BLOCKS)
        UserWeek.objects.bulk_create(self.WEEKS)
        PlannedDay.objects.bulk_create(self.DAYS)
        PlannedSession.objects.bulk_create(self.SESSIONS)


class CreateReturnToCyclingPackagePlan(BaseCreatePackagePlan):
    def __init__(self, user_package: UserPackage):
        self._reset_zone_difficulty_level(user_package.user_id)
        super().__init__(user_package)

        self.BUILD_WEEK_RAMP_RATE = 2.5
        self.RECOVERY_WEEK_RAMP_RATE = 0
        self.TOTAL_WEEKS_PER_BLOCK = 3

        self.STARTING_LOAD_FOR_PACKAGE = 15
        self._set_starting_load()

    @staticmethod
    def _reset_zone_difficulty_level(user_id):
        """For Return to Cycling Package, All difficulty levels are reset to 0"""
        zone_difficulty_level = ZoneDifficultyLevel.objects.filter(
            user_id=user_id, is_active=True
        ).last()
        zone_difficulty_level.reset_all_levels()
        zone_difficulty_level = create_new_model_instance(zone_difficulty_level)
        zone_difficulty_level.save()

    def _set_starting_load(self):
        self.user_personalise_data.starting_load = self.STARTING_LOAD_FOR_PACKAGE
        self.user_personalise_data.starting_acute_load = self.STARTING_LOAD_FOR_PACKAGE
        self.user_personalise_data.save()

    @staticmethod
    def _is_pad_applicable(week, day, selected_session):
        """Padding is disabled for Return to Cycling Package"""
        return False


class CreateHillClimbPackagePlan(BaseCreatePackagePlan):
    def __init__(self, user_package: UserPackage, package_duration: int):
        self.package_duration = package_duration
        super().__init__(user_package)

        self.TOTAL_WEEKS_PER_BLOCK = 4  # HC Pack has strictly 4 weeks per block
        self.BUILD_WEEK_RAMP_RATE = BUILD_WEEK_RAMP_RATE
        self.RECOVERY_WEEK_RAMP_RATE = RECOVERY_WEEK_RAMP_RATE

    def _get_plan_end_date(self, plan_start_date):
        return plan_start_date + timedelta(self.package_duration)

    def _get_session_types_for_this_week(self, week):
        week_zone_focus = self.week_zone_focuses[self.WEEK_NO]
        session_types = HillClimbPackageWeekRules.get_session_types(week_zone_focus)
        return session_types

    def _get_week_zone_focuses(self) -> list:
        package_duration_in_week = self.package_duration / 7
        weeks = eval(self.sub_package.week_zone_focuses)
        for total_weeks, week_zone_focuses in weeks:
            if total_weeks == package_duration_in_week:
                return week_zone_focuses

        raise ValueError(
            f"Failed to fetch week zone focuses. "
            f"total_weeks: {package_duration_in_week},"
            f"sub_package_id: {self.sub_package.id}"
        )


class UpdatePackagePlan:
    def __init__(
        self,
        user_auth,
        user_weeks_to_update=None,
        auto_update_start_date=None,
        is_utp=True,
    ):
        self.user_auth = user_auth

        self.auto_update_start_date = (
            auto_update_start_date or get_auto_update_start_date()
        )
        self.weeks_to_update = (
            user_weeks_to_update
            or UserWeek.objects.filter(
                user_block__user_auth=self.user_auth,
                start_date__gte=self.auto_update_start_date,
                is_active=True,
            ).order_by("start_date")[:4]
        )
        self.is_utp = is_utp

        self.user_plan = (
            self.user_auth.user_plans.filter(
                is_active=True,
                end_date__gte=datetime.today(),
                user_package__isnull=False,
            )
            .select_related("user_package")
            .last()
        )
        self.package_goal_type = (
            self.user_plan.user_package.sub_package.package.goal_type
        )

        self.user_personalise_data = self.user_auth.personalise_data.filter(
            is_active=True
        ).last()
        self.training_availability_object = TrainingAvailability(self.user_auth)
        self.zone_difficulty_service = ZoneDifficultyService(
            self.user_auth, self.user_personalise_data
        )

        self.BLOCKS = []
        self.WEEKS = []
        self.DAYS = []
        self.SESSIONS = []

        self.BLOCK_NO = 0
        self.WEEK_NO = 0
        self.DAY_NO = 0
        self.SESSION_NO = 0

        self.current_week = None
        self.current_day = None

    def get_last_sunday_load(self):
        week = self.WEEKS[-1]
        return week.sunday_max_load

    def get_yesterday(self, day):
        if len(self.DAYS) > 0:
            return self.DAYS[-1]
        yesterday_date = day.activity_date - timedelta(days=1)
        # TODO Refactor with in memory query
        yesterday = PlannedDay.objects.filter(
            user_auth=self.user_auth, activity_date=yesterday_date, is_active=True
        ).last()
        if yesterday:
            yesterday.selected_session = PlannedSession.objects.filter(
                user_auth=self.user_auth, session_date_time=yesterday.activity_date
            ).last()
        return yesterday

    def user_had_session_for_last_three_days(self):
        if len(self.DAYS) < 3:
            return False
        d1_session = self.DAYS[-1].selected_session
        d2_session = self.DAYS[-2].selected_session
        d3_session = self.DAYS[-3].selected_session

        session_type_codes = [
            d1_session.session_type.code,
            d2_session.session_type.code,
            d3_session.session_type.code,
        ]
        return not bool("REST" in session_type_codes)

    def create_week(
        self,
        week_start_date,
        week_end_date,
        block,
        zone_focus,
        week_type,
        starting_week,
    ):
        try:
            week = UserWeek(
                user_auth=self.user_auth,
                start_date=week_start_date,
                end_date=week_end_date,
                user_block=block,
                week_type=week_type,
                user_id=self.user_auth.code,
                zone_focus=zone_focus,
                week_code=uuid.uuid4(),
                block_code=block.block_code,
            )
            if week_type == "RECOVERY":
                week_ramp_rate = -2
            else:
                week_ramp_rate = 2.5

            if week.start_date <= self.auto_update_start_date:
                yesterday_date = self.auto_update_start_date - timedelta(days=1)
                query_conditions = {
                    "user_auth": self.user_auth,
                    "activity_date": yesterday_date,
                    "is_active": True,
                }
                if self.is_utp:
                    previous_day_load = (
                        ActualDay.objects.filter(**query_conditions)
                        .values("actual_load")
                        .last()
                        .get("actual_load")
                    )
                else:
                    previous_day_load = (
                        PlannedDay.objects.filter(**query_conditions)
                        .values("planned_load")
                        .last()
                        .get("planned_load")
                    )

                if previous_day_load is None:
                    previous_day_load = self.user_personalise_data.starting_load
                starting_load = max(MIN_STARTING_LOAD, previous_day_load)

                target_ramp_calculation_date = self.auto_update_start_date
            elif starting_week:
                target_ramp_calculation_date = self.user_plan.start_date
                starting_load = self.user_personalise_data.starting_load
            else:
                target_ramp_calculation_date = week.start_date
                starting_load = self.WEEKS[-1].sunday_max_load
            ramp_rate = get_calculated_ramp_rate(
                target_ramp_calculation_date, week_ramp_rate
            )
            week.sunday_max_load = starting_load + Decimal.from_float(ramp_rate)
            week_commute_pss = get_commute_pss_for_week(
                self.training_availability_object
            )
            week.commute_pss_week = (
                week_commute_pss  # this is a constant value refactor this
            )

            self.WEEK_NO += 1
            week.temp_week_no = self.WEEK_NO

            # create days of this week
            self.create_week_days(week)
            week.sunday_max_load = self.DAYS[-1].planned_load

            self.WEEKS.append(week)

        except Exception as e:
            week = None
            logger.exception(
                "Failed to create week in update training plan",
                extra=log_extra_fields(
                    user_auth_id=self.user_auth.id,
                    exception_message=str(e),
                    service_type=ServiceType.INTERNAL.value,
                ),
            )
        return week

    def create_week_days(self, week):
        _date = week.end_date
        target_load = week.sunday_max_load

        week_days = []
        number_of_week_days = get_number_of_week_days(week)
        for _ in range(number_of_week_days):
            if _date < self.auto_update_start_date:
                continue

            day = PlannedDay(
                user_auth=self.user_auth,
                activity_date=_date,
                max_load=target_load,
                week_code=week.week_code,
                day_code=uuid.uuid4(),
                user_id=self.user_auth.code,
            )

            _date = day.activity_date - timedelta(days=1)
            day.temp_week_no = self.WEEK_NO
            week_days.append(day)

            target_load = calculate_target_load(day.max_load)

        days_with_session, sessions = self.select_sessions_for_week_days(
            week, week_days[::-1]
        )
        self.SESSIONS += sessions
        return days_with_session

    def check_rest_day(self, day, available_training_hour):
        return (
            self.user_had_session_for_last_three_days()
            or available_training_hour < MIN_AVAILABLE_TRAINING_HOUR
            or get_minimum_pss(day) < PSS_SL_MIN
        )

    def _set_as_rest_day(self, day, utp, actual_yesterday, auto_update_start_date=None):
        rest_session = get_rest_session()
        session_type = get_session_type_by_session(rest_session)
        session = create_session_for_day(
            rest_session, session_type, day, None, padding=False
        )
        day = final_load_calculation_for_day(
            self.user_plan,
            day,
            session,
            actual_yesterday,
            self.user_personalise_data,
            utp,
            auto_update_start_date,
        )
        day.zone_focus = session.session_type.target_zone
        session.session = rest_session
        day.selected_session = session
        return day, session

    def select_build_session(
        self, week, week_days, day, pss_calc, available_training_hour, actual_yesterday
    ):
        session_types = get_session_types_for_this_week(week)
        planned_session = None
        for session_type in session_types:
            if (
                get_session_rule_by_session_type(session_type).typical_intensity
                > MAX_TYPICAL_INTENSITY
                and get_yesterdays_session_intensity(
                    day, self.is_utp, self.auto_update_start_date
                )
                > MAX_TYPICAL_INTENSITY
            ):
                continue
            number_of_sessions_of_this_type_in_this_week = (
                get_number_of_sessions_of_this_type_in_this_week(
                    week_days, session_type
                )
            )
            if (
                number_of_sessions_of_this_type_in_this_week
                >= get_session_rule_by_session_type(
                    session_type
                ).max_num_of_selected_session_type_per_week
            ):
                continue

            # training pss hours available calculations 2.10
            day.training_pss_by_hours = pss_calc.get_training_pss_available_hours(
                session_type,
                day,
                self.training_availability_object.user_available_hours,
            )

            # training pss final values calculations 2.11
            minimum_of_training_pss_calculations = min(
                day.training_pss_by_load,
                day.training_pss_by_freshness,
                day.training_pss_by_max_ride,
                day.training_pss_by_hours,
            )
            day.training_pss_final_value = minimum_of_training_pss_calculations

            selected_session = select_session(
                day, session_type, self.zone_difficulty_service
            )
            self.zone_difficulty_service.update_zone_difficulty_level(selected_session)

            if selected_session:
                padding = self._is_pad_applicable(week, day, selected_session)
                day.zone_focus = selected_session.session_type.target_zone
                planned_session = create_session_for_day(
                    selected_session=selected_session,
                    session_type=session_type,
                    day=day,
                    available_training_hour=available_training_hour,
                    padding=padding,
                )
                planned_session.session = selected_session
                day = final_load_calculation_for_day(
                    self.user_plan,
                    day,
                    planned_session,
                    actual_yesterday,
                    self.user_personalise_data,
                    utp=self.is_utp,
                    auto_update_start_date=self.auto_update_start_date,
                )
                break
        return day, planned_session

    def select_sessions_for_week_days(self, week, days):
        week_days = []
        selected_sessions = []
        try:
            for day in days:
                if day.activity_date < self.user_plan.start_date:
                    continue

                yesterday = self.get_yesterday(day)
                day.yesterday = yesterday
                actual_yesterday = None
                if yesterday:
                    actual_yesterday = ActualDay.objects.filter(
                        activity_date=yesterday.activity_date,
                        is_active=True,
                        user_auth=self.user_auth,
                    ).last()
                pss_calc = PssCalculation(
                    self.user_personalise_data, week, utp=self.is_utp
                )

                # commute pss calculation 2.1
                day.commute_pss_day = pss_calc.get_commute_pss_of_day(
                    day, self.training_availability_object.commute_days
                )

                # load and acute load calculation 2.4
                (
                    load_post_commute_nth_day,
                    acute_load_post_commute_nth_day,
                ) = pss_calc.get_load_and_acute_load_post_commute_nth_day(
                    day, actual_yesterday
                )
                day.load_post_commute = load_post_commute_nth_day
                day.acute_load_post_commute = acute_load_post_commute_nth_day

                # training pss load calculations 2.5
                day.training_pss_by_load = pss_calc.get_training_pss_load(
                    day, actual_yesterday
                )

                # training pss freshness calculations 2.6
                day.training_pss_by_freshness = pss_calc.get_training_pss_freshness(
                    day, actual_yesterday
                )

                # training pss max ride calculations 2.7
                day.training_pss_by_max_ride = pss_calc.get_training_pss_max_ride(
                    day, actual_yesterday
                )

                available_training_hour = self.training_availability_object.get_available_training_hour_for_day(
                    day.activity_date
                )

                if self.check_rest_day(day, available_training_hour):
                    day, session = self._set_as_rest_day(
                        day, self.is_utp, actual_yesterday, self.auto_update_start_date
                    )
                else:
                    day, session = self.select_build_session(
                        week,
                        week_days,
                        day,
                        pss_calc,
                        available_training_hour,
                        actual_yesterday,
                    )

                self.DAY_NO += 1
                day.temp_day_no = self.DAY_NO
                session.temp_day_no = day.temp_day_no
                selected_sessions.append(session)

                week.planned_pss = Decimal(week.planned_pss) + session.planned_pss
                day.selected_session = session
                week_days.append(day)
                self.DAYS.append(day)

        except Exception as e:
            logger.exception(
                "Failed to update training plan.",
                extra=log_extra_fields(
                    user_auth_id=self.user_auth.id,
                    exception_message=str(e),
                    service_type=ServiceType.INTERNAL.value,
                ),
            )
        return week_days, selected_sessions

    @transaction.atomic
    def run_auto_update_for_weeks(self):
        logger.info(
            "Updating user package",
            extra=log_extra_fields(
                user_auth_id=self.user_auth.id,
                user_id=self.user_auth.code,
                service_type=ServiceType.INTERNAL.value,
            ),
        )

        backup_days = None
        backup_sessions = None
        for week in self.weeks_to_update:
            update_is_active_value([week], False)

            planned_days_query_conditions = {
                "week_code": week.week_code,
                "is_active": True,
            }
            planned_sessions_query_conditions = {
                "session_date_time__date__range": (week.start_date, week.end_date),
                "is_active": True,
            }
            if week.start_date <= self.auto_update_start_date <= week.end_date:
                backup_days = PlannedDay.objects.filter(
                    activity_date__lt=self.auto_update_start_date,
                    week_code=week.week_code,
                    is_active=True,
                )
                backup_sessions = self.user_auth.planned_sessions.filter(
                    session_date_time__gte=week.start_date,
                    session_date_time__lt=self.auto_update_start_date,
                    is_active=True,
                )

                planned_days_query_conditions.update(
                    {"activity_date__gte": self.auto_update_start_date}
                )
                planned_sessions_query_conditions["session_date_time__date__range"] = (
                    self.auto_update_start_date,
                    week.end_date,
                )

            planned_days = PlannedDay.objects.filter(**planned_days_query_conditions)
            planned_sessions = self.user_auth.planned_sessions.filter(
                **planned_sessions_query_conditions
            )
            update_is_active_value(planned_days, False)
            update_is_active_value(planned_sessions, False)

            user_block = UserBlock.objects.get(
                block_code=week.block_code, is_active=True
            )
            starting_week = (
                self.user_plan.created_at.date() == self.auto_update_start_date
            )
            new_week = self.create_week(
                week.start_date,
                week.end_date,
                user_block,
                week.zone_focus,
                week.week_type,
                starting_week,
            )

            if backup_days and backup_sessions:
                backup_pss = 0
                for backup_day in backup_days:
                    backup_session = backup_sessions.filter(
                        session_date_time=backup_day.activity_date
                    ).last()
                    backup_session.day_code = backup_day.day_code
                    backup_session.save()
                    backup_pss += backup_sessions[0].planned_pss
                    backup_day.week_code = new_week.week_code
                    backup_day.save()
                new_week.planned_pss += backup_pss

                logger.info("Resetting backup days and sessions")
                backup_days = None
                backup_sessions = None

            user_blocks_updated_pss = (
                week.user_block.planned_pss
                - week.planned_pss
                + Decimal(new_week.planned_pss)
            )
            week.user_block.planned_pss = user_blocks_updated_pss
            week.user_block.save()

        weeks = self._save_updated_weeks()
        days = self._save_days(weeks)
        self._save_sessions(days)

        clear_user_cache(self.user_auth)

    def _is_pad_applicable(self, week, day, selected_session):
        if self.package_goal_type == GoalTypeEnum.LIFESTYLE.value[0]:
            return False

        if week.zone_focus == 0:
            return False
        return is_pad_applicable(day, selected_session)

    def _save_updated_weeks(self):
        weeks = UserWeek.objects.bulk_create(self.WEEKS)
        return weeks

    def _save_days(self, weeks):
        for day in self.DAYS:
            week = weeks[day.temp_week_no - 1]
            day.user_week = week
        days = PlannedDay.objects.bulk_create(self.DAYS)
        return days

    def _save_sessions(self, days):
        for session in self.SESSIONS:
            day = days[session.temp_day_no - 1]
            session.planned_day = day
        sessions = PlannedSession.objects.bulk_create(self.SESSIONS)
        return sessions


class PackageDurationService:
    @staticmethod
    def get_package_duration_list():
        duration_list = PackageDuration.list()
        caption = PACKAGE_DURATION_PAGE_CAPTION
        return {
            "captions": caption,
            "duration_list": duration_list,
        }


class PackageKnowledgeHubViewService:
    @staticmethod
    def get_package_knowledge_hub_base_contents(package_id):
        package = Package.objects.filter(pk=package_id).last()
        knowledge_hub_list = (
            KnowledgeHub.objects.filter(package_id=package_id, is_active=True)
            .values("id", "title")
            .order_by("id")
        )

        return {
            "app_bar_title": KNOWLEDGE_HUB_APP_BAR_TITLE,
            "header": package.knowledge_hub_title,  # As of R13, app_bar_title and header are always same
            "details": package.knowledge_hub_text,
            "knowledge_hub_list": knowledge_hub_list,
        }


class KnowledgeHubViewService:
    @staticmethod
    def get_knowledge_hub_contents(knowledge_hub_id):
        knowledge_hub = KnowledgeHub.objects.filter(
            pk=knowledge_hub_id, is_active=True
        ).last()
        title = knowledge_hub.title
        markdown_text_url = knowledge_hub.content_url

        return {
            "title": title,
            "markdown_text_url": markdown_text_url,
        }
