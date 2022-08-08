from datetime import date

from core.apps.common.utils import get_user_connected_table_instance
from core.apps.daily.models import ActualDay
from core.apps.daily.utils import (
    get_rides_completed_and_total,
    get_total_distance_covered_from_onboarding_day,
    get_upcoming_and_past_ride_dict_array,
)
from core.apps.evaluation.daily_evaluation.utils import get_event_target_prs
from core.apps.event.enums.performance_goal_enum import PerformanceGoalEnum
from core.apps.session.models import PlannedSession
from core.apps.user_auth.models import UserAuthModel

from ..user_profile.models import UserPersonaliseData
from ..user_profile.utils import (
    get_user_age,
    get_user_fthr,
    get_user_ftp,
    get_user_gender,
    get_user_max_heart_rate,
    get_user_weight,
)
from .dictionary import get_athlete_profile_dict, get_overview_dict


class AthleteService:
    @classmethod
    def get_athlete_info(cls, athlete_id):
        (
            user_auth,
            user_profile,
            user_personalise_data,
            user_event,
        ) = get_user_connected_table_instance(athlete_id)
        actual_day_data = ActualDay.objects.filter(
            user_auth=user_auth, activity_date=date.today(), is_active=True
        ).first()

        rides_completed, _ = get_rides_completed_and_total(user_auth)

        target_prs, _ = get_event_target_prs(
            user_event, PerformanceGoalEnum.get_text(user_event.performance_goal)
        )

        days_due_of_event = (user_event.start_date - date.today()).days

        total_distance = get_total_distance_covered_from_onboarding_day(user_auth)

        athlete_dict = get_athlete_profile_dict(
            athlete_id,
            user_profile,
            user_personalise_data,
            rides_completed,
            target_prs,
            days_due_of_event,
            user_auth.get_profile_picture(),
            actual_day_data,
            total_distance,
        )
        return athlete_dict

    @classmethod
    def get_athlete_overview(cls, id):
        user_auth = UserAuthModel.objects.filter(pk=id, is_active=True).first()
        planned_sessions = PlannedSession.objects.filter(
            user_auth=user_auth, is_active=True
        )
        timezone_offset = user_auth.timezone_offset

        (
            upcoming_rides_dict_arr,
            past_rides_dict_arr,
        ) = get_upcoming_and_past_ride_dict_array(
            planned_sessions, date.today(), timezone_offset
        )

        overview_dict = get_overview_dict(upcoming_rides_dict_arr, past_rides_dict_arr)

        return overview_dict

    @classmethod
    def get_athlete_baseline_fitness(cls, user_id, activity_datetime):
        user_auth = UserAuthModel.objects.filter(id=user_id).first()
        user_ftp = get_user_ftp(user_auth, activity_datetime)
        user_fthr = get_user_fthr(user_auth, activity_datetime)
        user_max_hr = get_user_max_heart_rate(user_auth, activity_datetime)

        return {
            "athlete_ftp": user_ftp,
            "athlete_fthr": user_fthr,
            "athlete_max_hr": user_max_hr,
        }

    @classmethod
    def get_athlete_file_process_info(cls, user_id, activity_datetime):
        user_auth = UserAuthModel.objects.filter(id=user_id).first()
        user_ftp = get_user_ftp(user_auth, activity_datetime)
        user_fthr = get_user_fthr(user_auth, activity_datetime)
        user_max_hr = get_user_max_heart_rate(user_auth, activity_datetime)
        user_weight = get_user_weight(user_auth, activity_datetime)
        user_gender = get_user_gender(user_auth, activity_datetime)
        user_age = get_user_age(user_auth, activity_datetime)
        timezone_offset = user_auth.timezone_offset

        return {
            "athlete_ftp": user_ftp,
            "athlete_fthr": user_fthr,
            "athlete_max_hr": user_max_hr,
            "athlete_weight": user_weight,
            "athlete_gender": user_gender,
            "athlete_age": user_age,
            "timezone_offset": timezone_offset,
        }

    @classmethod
    def get_athlete_file_process_info_list(cls, user_id):
        file_process_info_list = list(
            UserPersonaliseData.objects.filter(user_id=user_id)
            .all()
            .values("created_at", "updated_at", "weight")
        )
        return file_process_info_list


class CoachService:
    @classmethod
    def get_coach_info(cls, coach_id):
        (
            user_auth,
            user_profile,
            user_personalise_data,
            user_event,
        ) = get_user_connected_table_instance(coach_id)

        coach_dict = {
            "id": user_auth.id,
            "email": user_auth.email,
            "first_name": user_profile.name,
            "surname": user_profile.surname,
        }
        return coach_dict
