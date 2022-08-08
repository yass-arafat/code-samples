import datetime

from rest_framework import serializers

from core.apps.activities.utils import daroan_get_athlete_info
from core.apps.common.common_functions import CommonClass
from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.user_auth.models import UserAuthModel

from ...enums.gender_enum import GenderEnum
from ...enums.user_unit_system_enum import UserUnitSystemEnum
from ...models import ProfileImage, TimeZone, UserPersonaliseData, UserProfile


class UserSettingsSerializer(serializers.ModelSerializer):
    settings_data = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ("settings_data",)

    def get_settings_data(self, user_profile):
        user_code = self.context["user_code"]
        user_personalise_data = UserPersonaliseData.objects.filter(
            user_id=user_code, is_active=True
        ).last()
        # user_scheduled_data = UserTrainingAvailability.objects.filter(
        #     user_id=user_code
        # ).last()

        timezone_list_dict = CommonClass.get_time_zone_list_dict(
            TimeZone.objects.filter(is_active=True)
        )
        user_local_date = DateTimeUtils.get_user_local_date_from_utc(
            self.context["timezone_offset"], datetime.datetime.now()
        )
        # user_info_from_dakghor = dakghor_get_athlete_info(user_code)
        user_info_from_daroan = daroan_get_athlete_info(user_code)["data"]

        # has_garmin_workout_export_permission = (
        #     False
        #     if not user_info_from_dakghor
        #     else user_info_from_dakghor["workout_import_permission"]
        # )

        settings_data = {
            "timezone_list": timezone_list_dict,
            "profile_data": {
                "joining_date": user_info_from_daroan["joining_date"],
                "first_name": user_profile.name,
                "surname": user_profile.surname,
                "email": user_info_from_daroan["email"],
                "gender": GenderEnum.get_name(user_profile.gender)
                if user_profile.gender
                else None,
                "dob": user_personalise_data.date_of_birth,
                "weight": user_personalise_data.weight,
                "unit_preferences": UserUnitSystemEnum.get_name(
                    user_profile.unit_system
                ),
                "timezone": {
                    "timezone_id": user_profile.timezone.id,
                    "timezone_name": user_profile.timezone.name,
                    "timezone_offset": user_profile.timezone.offset,
                    "timezone_type": user_profile.timezone.type,
                },
            },
            # "goal_data": self._get_goal_data(user_local_date),
            # "availability_data": {
            #     "commute_to_work": user_scheduled_data.commute_to_work_by_bike,
            #     "single_commute_duration": user_scheduled_data.duration_single_commute_in_hours,
            #     "commute_weekdays": user_scheduled_data.days_commute_by_bike_list,
            #     "training_hour_per_day": user_scheduled_data.training_availability_list,
            # }
            # if user_scheduled_data
            # else {
            #     "commute_to_work": False,
            #     "single_commute_duration": 0.0,
            #     "commute_weekdays": [False, False, False, False, False, False, False],
            #     "training_hour_per_day": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            # },
            "fitness_data": {
                "ftp": user_personalise_data.current_ftp
                if user_personalise_data.current_ftp
                else None,
                "threshold_hr": user_personalise_data.current_fthr
                if user_personalise_data.current_fthr
                else None,
                "maximum_hr": user_personalise_data.max_heart_rate
                if user_personalise_data.max_heart_rate
                else None,
                "load": user_personalise_data.starting_load,
                "acute_load": user_personalise_data.starting_acute_load,
            }
            if user_personalise_data
            else {},
            # "platform_data": {
            #     "garmin_linked": user_info_from_dakghor["is_garmin_connected"],
            #     "strava_linked": user_info_from_dakghor["is_strava_connected"],
            #     "wahoo_linked": user_info_from_dakghor["is_wahoo_connected"],
            #     "has_garmin_workout": has_garmin_workout_export_permission,
            # }
            # if user_info_from_dakghor
            # else None,
            "user_local_date": user_local_date,
        }

        # settings_data["profile_data"][
        #     "previous_goal_completed"
        # ] = is_previous_goal_completed(user_auth)

        # Below data are needed for simulator portal only
        # Training hours of 4 weeks are stored in a string. We have to retrieve one
        # week's hours from it
        settings_data["fitness_data"]["training_history"] = (
            float(
                user_personalise_data.training_hours_over_last_4_weeks.split(",")[0][1:]
            )
            if user_personalise_data.training_hours_over_last_4_weeks
            else None
        )
        return settings_data

    # def _get_goal_data(self, user_local_date):
    #     if not has_pro_feature_access(self.context["user_subscription_status"]):
    #         return {}
    #     user_plan = UserPlan.objects.filter_with_goal(
    #         user_id=self.context["user_code"],
    #         end_date__gte=user_local_date,
    #         is_active=True,
    #     ).last()
    #
    #     if not user_plan:
    #         return {}
    #
    #     days_due_of_event = user_plan.days_due_of_event(user_local_date)
    #     goal_data = {
    #         "days_remaining_till_event": days_due_of_event,
    #     }
    #
    #     if user_plan.user_event_id:
    #         user_event = user_plan.user_event
    #         event_duration_in_days = self._event_duration_in_days(
    #             user_event.start_date, user_event.end_date
    #         )
    #         event_type = EventTypeEnum.get_capitalized_name(user_event.event_type.type)
    #         goal_data.update(
    #             {
    #                 "event_name": user_event.name,
    #                 "event_distance": int(user_event.distance_per_day),
    #                 "goal": PerformanceGoalEnum.get_text(user_event.performance_goal),
    #                 "event_duration_in_days": event_duration_in_days,
    #                 "event_type": event_type,
    #                 "event_date": user_event.start_date,
    #             }
    #         )
    #     elif user_plan.user_package_id:
    #         user_package = user_plan.user_package
    #         goal_data.update(
    #             {
    #                 "event_name": user_package.sub_package.name,
    #                 "event_date": user_plan.end_date,
    #             }
    #         )
    #     return goal_data

    # def _event_duration_in_days(self, start_date, end_date):
    #     """
    #     Calculate the duration of the event in days with the start and end date
    #     """
    #     return (end_date - start_date).days + 1


class ProfileImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProfileImage
        fields = ("url",)

    def get_url(self, profile_image):
        return profile_image.avatar.url


class ProfileImageSerializer2(serializers.ModelSerializer):
    class Meta:
        model = ProfileImage
        fields = "__all__"


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuthModel
        fields = ("email",)


class UserPersonaliseDataSerializer(serializers.ModelSerializer):
    training_hours_over_last_4_weeks = serializers.SerializerMethodField()
    max_heart_rate = serializers.SerializerMethodField()

    class Meta:
        model = UserPersonaliseData
        fields = (
            "training_hours_over_last_4_weeks",
            "current_ftp",
            "current_fthr",
            "max_heart_rate",
            "ftp_input_denied",
            "fthr_input_denied",
        )

    def get_training_hours_over_last_4_weeks(self, personalise_data):
        training_hours = eval(personalise_data.training_hours_over_last_4_weeks)
        average_hour = sum(training_hours) / 4
        return average_hour

    def get_max_heart_rate(self, personalise_data):
        if personalise_data.max_heart_rate == 0:
            return None
        else:
            return personalise_data.max_heart_rate


class BaselineFitnessSerializer(serializers.ModelSerializer):
    current_ftp = serializers.SerializerMethodField()
    current_threshold_heart_rate = serializers.SerializerMethodField()
    max_heart_rate = serializers.SerializerMethodField()

    class Meta:
        model = UserPersonaliseData
        fields = ("current_ftp", "current_threshold_heart_rate", "max_heart_rate")

    def get_current_ftp(self, personalise_data):
        return personalise_data.current_ftp or None

    def get_current_threshold_heart_rate(self, personalise_data):
        return personalise_data.current_fthr or None

    def get_max_heart_rate(self, personalise_data):
        return personalise_data.max_heart_rate or None
