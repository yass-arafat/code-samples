from rest_framework import serializers

from core.apps.common.messages import CALENDAR_RECOVERY_TILE_MESSAGE
from core.apps.plan.enums.session_status_enum import (
    SessionLabelEnum,
    SessionLabelTypeEnum,
    SessionStatusEnum,
    SessionTypeEnum,
)
from core.apps.session.models import ActualSession, PlannedSession


class DayActualSessionSerializer(serializers.ModelSerializer):
    session_metadata = serializers.SerializerMethodField()
    session_date_time = serializers.SerializerMethodField()
    session_name = serializers.SerializerMethodField()
    session_message = serializers.SerializerMethodField()
    session_timespan = serializers.SerializerMethodField()
    session_distance = serializers.SerializerMethodField()
    session_score = serializers.SerializerMethodField()
    session_accuracy_score = serializers.SerializerMethodField()
    session_pss = serializers.SerializerMethodField()
    zone_focus = serializers.SerializerMethodField()

    class Meta:
        model = ActualSession
        fields = (
            "session_metadata",
            "session_date_time",
            "session_name",
            "session_message",
            "zone_focus",
            "session_pss",
            "session_timespan",
            "session_distance",
            "session_score",
            "session_accuracy_score",
        )

    def get_session_metadata(self, actual_session):
        from core.apps.session.utils import get_session_metadata

        planned_session = actual_session.planned_session
        return get_session_metadata(actual_session, planned_session=planned_session)

    def get_session_date_time(self, actual_session):
        return actual_session.session_date_time

    def get_session_name(self, actual_session):
        from core.apps.session.utils import get_session_name

        planned_session = actual_session.planned_session
        session_date_time = actual_session.session_date_time

        # If planned_session exists, then activity_type is not required to retrieve the session name
        activity_type = actual_session.activity_type if not planned_session else None

        return get_session_name(
            actual_session,
            planned_session,
            session_date_time,
            activity_type=activity_type,
        )

    def get_session_message(self, actual_session):
        if actual_session.actual_duration == 0:
            return CALENDAR_RECOVERY_TILE_MESSAGE
        return None

    def get_session_timespan(self, actual_session):
        return round(actual_session.actual_duration * 60)

    def get_session_score(self, actual_session):
        if not actual_session.actual_duration:
            return None
        session_score = actual_session.session_score
        return session_score.get_overall_score() if session_score else None

    def get_session_accuracy_score(self, actual_session):
        if not actual_session.actual_duration:
            return None
        session_score = actual_session.session_score
        return session_score.get_overall_accuracy_score() if session_score else None

    def get_session_pss(self, actual_session):
        return round(actual_session.actual_pss)

    def get_session_distance(self, actual_session):
        actual_distance = actual_session.actual_distance_in_meters / 1000  # meter to Km
        distance = str(round(actual_distance, 1))
        return distance + " km"

    def get_zone_focus(self, actual_session):
        planned_session = actual_session.planned_session
        if planned_session:
            return planned_session.zone_focus
        return None


class DayPlannedSessionSerializer(serializers.ModelSerializer):
    session_metadata = serializers.SerializerMethodField()
    session_date_time = serializers.SerializerMethodField()
    session_name = serializers.SerializerMethodField()
    session_message = serializers.SerializerMethodField()
    session_timespan = serializers.SerializerMethodField()
    session_pss = serializers.SerializerMethodField()
    session_elevation = serializers.SerializerMethodField()
    session_distance = serializers.SerializerMethodField()
    intervals = serializers.SerializerMethodField()

    class Meta:
        model = PlannedSession
        fields = (
            "session_metadata",
            "session_date_time",
            "session_name",
            "session_message",
            "zone_focus",
            "session_timespan",
            "session_pss",
            "session_distance",
            "session_elevation",
            "intervals",
        )

    def is_event_session(self, planned_session):
        event_dates = self.context.get("event_dates")
        return event_dates and planned_session.session_date_time.date() in event_dates

    def get_session_metadata(self, planned_session):
        if self.is_event_session(planned_session):
            session_label_type = SessionLabelTypeEnum.EVENT.value
            session_type = SessionTypeEnum.CYCLING.value
            session_label = SessionLabelEnum.PLANNED_EVENT.value
        else:
            session_label_type = SessionLabelTypeEnum.TRAINING_SESSION.value
            session_type = (
                SessionTypeEnum.RECOVERY.value
                if planned_session.is_recovery_session()
                else SessionTypeEnum.CYCLING.value
            )
            session_label = SessionLabelEnum.PLANNED_SESSION.value

        return {
            "planned_id": planned_session.id,
            "session_type": session_type.upper(),
            "session_status": SessionStatusEnum.PLANNED.value,
            "session_label": session_label,
            "session_label_type": session_label_type,
        }

    def get_session_date_time(self, planned_session):
        return planned_session.session_date_time

    def get_session_name(self, planned_session):
        if self.is_event_session(planned_session):
            return planned_session.user_plan.user_event.name
        return planned_session.name

    def get_session_message(self, planned_session):
        if planned_session.is_recovery_session():
            return CALENDAR_RECOVERY_TILE_MESSAGE

    def get_session_timespan(self, planned_session):
        return int(planned_session.planned_duration * 60)

    def get_session_pss(self, planned_session):
        return round(planned_session.planned_pss)

    def get_session_distance(self, planned_session):
        if self.is_event_session(planned_session):
            distance = str(
                round(planned_session.user_plan.user_event.distance_per_day, 1)
            )
            return distance + " km"

    def get_session_elevation(self, planned_session):
        if self.is_event_session(planned_session):
            elevation = str(
                round(planned_session.user_plan.user_event.elevation_gain, 0)
            )
            return elevation + " m"

    def get_intervals(self, planned_session):
        from core.apps.session.services import SetsAndRepsService

        if planned_session.zone_focus != 0:
            return SetsAndRepsService(
                self.context["user"],
                planned_session.session.code,
                planned_session.pad_time_in_seconds,
            ).get_session_sets_and_reps()
