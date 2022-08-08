from rest_framework import serializers

from core.apps.common.services import RoundServices
from core.apps.week.models import WeekAnalysis


class WeekAnalysisReportSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    is_feedback_saved = serializers.SerializerMethodField("check_feedback_saved")
    week_sub_title = serializers.SerializerMethodField("week_title")
    distance = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    elevation = serializers.SerializerMethodField()

    class Meta:
        model = WeekAnalysis
        fields = (
            "id",
            "is_feedback_saved",
            "week_no",
            "total_weeks_in_block",
            "week_sub_title",
            "week_start_date",
            "week_end_date",
            "current_week_remarks",
            "last_week_comparison_remarks",
            "tips_for_next_week",
            "distance",
            "duration",
            "elevation",
            "total_rides",
            "pss",
            "is_ftp_available",
            "is_fthr_available",
            "planned_time_in_power_zones",
            "actual_time_in_power_zones",
            "planned_time_in_hr_zones",
            "actual_time_in_hr_zones",
            "feel_feedback",
            "week_feedback",
            "suggestion_feedback",
            "utp_summary",
            "utp_reason",
        )

    def get_id(self, week_analysis):
        return week_analysis.code

    def check_feedback_saved(self, week_analysis):
        return week_analysis.is_feedback_saved()

    def week_title(self, week_analysis):
        return week_analysis.week_title

    def get_distance(self, week_analysis):
        return f"{RoundServices.round_distance(week_analysis.distance/1000)} km"

    def get_duration(self, week_analysis):
        return week_analysis.duration * 60  # converting to seconds

    def get_elevation(self, week_analysis):
        return f"{week_analysis.elevation} m"

    def get_utp_summary(self, week_analysis):
        return week_analysis.utp_summary

    def get_utp_reason(self, week_analysis):
        return week_analysis.utp_reason
