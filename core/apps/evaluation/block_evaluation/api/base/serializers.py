from rest_framework import serializers

from core.apps.common.date_time_utils import DateTimeUtils
from core.apps.session.models import PlannedSession


class UserBlockSessionSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    session_type_name = serializers.SerializerMethodField()
    session_name = serializers.SerializerMethodField()
    planned_duration = serializers.SerializerMethodField()
    actual_duration = serializers.SerializerMethodField()
    overall_score = serializers.SerializerMethodField()
    prs_score = serializers.SerializerMethodField()
    overall_accuracy_score = serializers.SerializerMethodField()
    prs_accuracy_score = serializers.SerializerMethodField()

    class Meta:
        model = PlannedSession
        fields = (
            "id",
            "date",
            "session_type_name",
            "planned_duration",
            "actual_duration",
            "is_evaluation_done",
            "session_name",
            "zone_focus",
            "overall_score",
            "prs_score",
            "is_completed",
            "overall_accuracy_score",
            "prs_accuracy_score",
        )

    def get_date(self, user_session):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_from_utc(
            offset, user_session.session_date_time
        )

    def get_session_type_name(self, user_session):
        return user_session.session_type_name

    def get_session_name(self, user_session):
        return user_session.name

    def get_planned_duration(self, user_session):
        return user_session.planned_duration / 60

    def get_overall_score(self, user_session):
        actual_session = user_session.actual_session
        if actual_session:
            return actual_session.session_score.get_overall_score()
        return None

    def get_prs_score(self, user_session):
        actual_session = user_session.actual_session
        if actual_session:
            return actual_session.session_score.get_prs_score()
        return None

    def get_overall_accuracy_score(self, user_session):
        actual_session = user_session.actual_session
        if actual_session:
            return actual_session.session_score.get_overall_accuracy_score()
        return None

    def get_prs_accuracy_score(self, user_session):
        actual_session = user_session.actual_session
        if actual_session:
            return actual_session.session_score.get_prs_accuracy_score()
        return None

    def get_actual_duration(self, user_session):
        actual_session = user_session.actual_session
        if actual_session:
            return actual_session.actual_duration / 60
        return 0.0
