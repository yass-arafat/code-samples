import json

from django.utils.dateformat import DateFormat
from rest_framework import serializers

from core.apps.activities.utils import dakghor_get_athlete_activity
from core.apps.common.const import MTP_OVER_TRAINING_INTENSITY as MTI
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.messages import (
    CALENDAR_RECOVERY_TILE_MESSAGE,
    I_AM_AWAY_TILE_DELETE_MESSAGE,
    I_AM_AWAY_TILE_DELETE_MESSAGE_PLURAL,
    I_AM_AWAY_TILE_MESSAGE,
    I_AM_AWAY_TILE_MESSAGE_PLURAL,
    UNPLANNED_SESSION_MESSAGE,
)
from core.apps.event.enums.event_type_enum import EventTypeEnum
from core.apps.session.enums.session_pairing_message_enum import SessionPairingMessage
from core.apps.session.models import ActualSession, PlannedSession
from core.apps.session.utils import get_session_label, get_session_name

from ...enums.session_status_enum import (
    SessionLabelEnum,
    SessionLabelTypeEnum,
    SessionNameEnum,
    SessionStatusEnum,
    SessionTypeEnum,
)


class GetMyMonthPlanSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    session_name = serializers.SerializerMethodField()
    session_type = serializers.SerializerMethodField()
    session_edit_options = serializers.SerializerMethodField()
    planned_duration = serializers.SerializerMethodField()
    actual_duration = serializers.SerializerMethodField()
    overall_score = serializers.SerializerMethodField()
    overall_accuracy_score = serializers.SerializerMethodField()
    prs_score = serializers.SerializerMethodField()
    prs_accuracy_score = serializers.SerializerMethodField()

    class Meta:
        model = PlannedSession
        fields = (
            "id",
            "date",
            "session_name",
            "session_type",
            "zone_focus",
            "is_completed",
            "planned_duration",
            "actual_duration",
            "session_edit_options",
            "is_evaluation_done",
            "overall_score",
            "prs_score",
            "prs_accuracy_score",
            "overall_accuracy_score",
        )

    def get_date(self, planned_session):
        return planned_session.session_date_time.date()

    def get_session_name(self, user_planned_session):
        return user_planned_session.name

    def get_session_type(self, user_planned_session):
        user_actual_sessions = self.context["user_actual_sessions"]
        if user_planned_session.is_recovery_session() and user_actual_sessions.filter(
            session_code__isnull=True,
            session_date_time__date=user_planned_session.session_date_time.date(),
        ):
            return UNPLANNED_SESSION_MESSAGE
        return user_planned_session.session_type.name

    def get_session(self, planned_sessions, day, today):
        session = planned_sessions.filter(day_code=day.day_code).first()
        if session:
            if (
                day.activity_date < today and not session.is_completed
            ):  # if past day session is not completed then it is a rest day
                return None
            else:
                return session
        else:
            return None

    def check_over_training(
        self, week, week_days_intensities, day, today, planned_sessions, movable_session
    ):
        consecutive_days = [day]
        total_intensity = movable_session.planned_intensity
        previous_day = day.previous_day
        while previous_day:
            if (
                previous_day.activity_date < week.start_date
                or previous_day == movable_session.day
            ):
                break
            previous_day_session = self.get_session(
                planned_sessions, previous_day, today
            )
            if previous_day and previous_day_session:
                consecutive_days.append(previous_day)
                if previous_day_session.is_completed:
                    total_intensity += (
                        previous_day_session.actual_session.actual_intensity
                    )
                else:
                    total_intensity += previous_day_session.planned_intensity
            else:
                break
            previous_day = previous_day.previous_day

        next_day = day.next_day
        while next_day:
            if (
                next_day.activity_date > week.end_date
                or next_day == movable_session.day
            ):
                break
            next_day_session = self.get_session(planned_sessions, next_day, today)
            if next_day and next_day_session:
                consecutive_days.append(next_day)
                total_intensity = total_intensity + next_day_session.planned_intensity
            else:
                break
            next_day = next_day.next_day

        # high intensity condition
        high_intensity_days = False
        intensities = week_days_intensities
        day_no = day.activity_date.weekday()
        intensities[day_no] = intensities[movable_session.day.activity_date.weekday()]
        intensities[movable_session.day.activity_date.weekday()] = 0
        if (
            (
                (day_no + 1 <= 6 and day_no + 2 <= 6 and not high_intensity_days)
                and (
                    intensities[day_no] > MTI
                    and intensities[day_no + 1] > MTI
                    and intensities[day_no + 2] > MTI
                )
            )
            or (
                (day_no + 1 <= 6 and day_no - 1 >= 0 and not high_intensity_days)
                and (
                    intensities[day_no] > MTI
                    and intensities[day_no + 1] > MTI
                    and intensities[day_no - 1] > MTI
                )
            )
            or (
                (day_no - 1 >= 0 and day_no - 2 >= 0 and not high_intensity_days)
                and (
                    intensities[day_no] > MTI
                    and intensities[day_no - 1] > MTI
                    and intensities[day_no - 2] > MTI
                )
            )
        ):
            high_intensity_days = True

        if len(consecutive_days) > 3:
            return "RECOVERY"
        elif high_intensity_days:
            return "HIGH_INTENSITY"
        return None

    def get_movable_days(
        self,
        week,
        today,
        movable_session,
        session_movable_days,
        user_planned_sessions,
        current_week_planned_sessions,
        week_days_session_intensities,
    ):
        movable_days = []
        for day in session_movable_days:
            session = current_week_planned_sessions[day.day_code]
            if session and session.zone_focus == 0:
                over_training_message = self.check_over_training(
                    week,
                    week_days_session_intensities,
                    day,
                    today,
                    user_planned_sessions,
                    movable_session,
                )
                movable_days.append(
                    {
                        "day_id": day.id,
                        "date": day.activity_date,
                        "day_name": day.activity_date.strftime("%A"),
                        "over_training": over_training_message,
                    }
                )
        return movable_days

    def check_cancellable(self, user_session, week, today, is_completed_day):
        if (
            user_session.zone_focus != 0
            and is_completed_day is False
            and (today <= user_session.session_date_time.date() <= week.end_date)
        ):
            return True
        else:
            return False

    def check_movable(self, user_session, week, is_completed_day):
        if (
            user_session.zone_focus != 0
            and is_completed_day is False
            and (
                week.start_date
                <= user_session.session_date_time.date()
                <= week.end_date
            )
        ):
            return True
        else:
            return False

    def get_session_edit_options(self, user_session):
        week = self.context["current_week"]
        today = self.context["user_today"]
        session_is_movable = False
        session_is_cancellable = False
        movable_days = []

        is_completed_day = self.context["is_completed_day"]
        if week:
            if (
                week.start_date
                <= user_session.session_date_time.date()
                <= week.end_date
                and not user_session.is_recovery_session()
            ):
                session_is_cancellable = self.check_cancellable(
                    user_session, week, today, is_completed_day
                )
                session_is_movable = self.check_movable(
                    user_session, week, is_completed_day
                )
                if session_is_movable:
                    week_days_session_intensities = self.context[
                        "week_days_session_intensities"
                    ]
                    session_movable_days = self.context["session_movable_days"]
                    current_week_planned_sessions = self.context[
                        "current_week_planned_sessions"
                    ]
                    user_planned_sessions = self.context["user_planned_sessions"]
                    movable_days = self.get_movable_days(
                        week,
                        today,
                        user_session,
                        session_movable_days,
                        user_planned_sessions,
                        current_week_planned_sessions,
                        week_days_session_intensities,
                    )

        return {
            "is_cancellable": session_is_cancellable,
            "is_movable": session_is_movable,
            "movable_days": movable_days,
        }

    def get_planned_duration(self, user_session):
        return user_session.planned_duration / 60

    def get_actual_duration(self, user_session):
        actual_session = user_session.actual_session
        if actual_session:
            return actual_session.actual_duration / 60
        return 0.0

    def get_overall_score(self, user_session):
        actual_session = user_session.actual_session
        return (
            actual_session.session_score.get_overall_score() if actual_session else None
        )

    def get_overall_accuracy_score(self, user_session):
        actual_session = user_session.actual_session
        return (
            actual_session.session_score.get_overall_accuracy_score()
            if actual_session
            else None
        )

    def get_prs_score(self, user_session):
        actual_session = user_session.actual_session
        return actual_session.session_score.get_prs_score() if actual_session else None

    def get_prs_accuracy_score(self, user_session):
        actual_session = user_session.actual_session
        return (
            actual_session.session_score.get_prs_accuracy_score()
            if actual_session
            else None
        )


class ActualSessionSerializer(serializers.ModelSerializer):
    session_metadata = serializers.SerializerMethodField()
    session_date_time = serializers.SerializerMethodField()
    session_name = serializers.SerializerMethodField()
    session_edit_options = serializers.SerializerMethodField()
    session_timespan = serializers.SerializerMethodField()
    session_distance = serializers.SerializerMethodField()
    session_elevation = serializers.SerializerMethodField()
    session_score = serializers.SerializerMethodField()
    session_accuracy_score = serializers.SerializerMethodField()
    session_pss = serializers.SerializerMethodField()
    zone_focus = serializers.SerializerMethodField()
    sensor_data = serializers.SerializerMethodField()
    third_party_code = serializers.SerializerMethodField()
    show_pairing_option = serializers.SerializerMethodField()
    planned_session_name = serializers.SerializerMethodField()
    pairing_option_message = serializers.SerializerMethodField()

    class Meta:
        model = ActualSession
        fields = (
            "session_metadata",
            "session_date_time",
            "session_name",
            "zone_focus",
            "session_timespan",
            "session_edit_options",
            "session_distance",
            "session_score",
            "session_pss",
            "sensor_data",
            "session_accuracy_score",
            "session_code",
            "session_elevation",
            "third_party_code",
            "show_pairing_option",
            "planned_session_name",
            "pairing_option_message",
        )

    def get_sensor_data(self, actual_session):
        activity_type = actual_session.activity_type

        ride_summary = None
        if actual_session.athlete_activity_code:
            athlete_activity = dakghor_get_athlete_activity(
                actual_session.athlete_activity_code
            ).json()["data"]["athlete_activity"]
            ride_summary = athlete_activity["ride_summary"]

        if (
            ride_summary is None
            or (  # ride summary will be None in case of manual activity
                activity_type
                and activity_type.lower() != ActivityTypeEnum.RUNNING.value[1].lower()
            )
        ):
            return {"average_heart_rate": None}

        ride_summary = ride_summary.replace("'", '"')
        ride_summaries = json.loads(ride_summary)
        for ride_summary in ride_summaries:
            if ride_summary["type"] == "Heart Rate":
                return {"average_heart_rate": round(ride_summary["average"])}

    def get_session_metadata(self, actual_session):
        # TODO: Try to make a single function for retrieving session metadata everywhere
        actual_id = actual_session.id
        planned_session = None
        if self.context["pro_feature_access"] and not self.context["user_away"]:
            planned_session = actual_session.get_planned_session_from_list(
                self.context["planned_sessions"]
            )

        planned_id = planned_session.id if planned_session else None
        activity_type = actual_session.activity_type.upper()
        session_label = get_session_label(actual_session, planned_id)

        if planned_id:
            if (
                planned_session.zone_focus == 0
                and actual_session.session_date_time.date()
                not in self.context["event_dates"]
            ):
                session_type = SessionTypeEnum.RECOVERY.value
                session_status = None
            else:
                session_type = activity_type
                session_status = SessionStatusEnum.PAIRED.value
        else:
            session_type = activity_type
            session_status = SessionStatusEnum.UNPAIRED.value

        return {
            "planned_id": planned_id,
            "actual_id": actual_id,
            "session_type": session_type.upper(),
            "session_status": session_status,
            "session_label": session_label,
            "session_label_type": actual_session.session_label,
        }

    def get_session_date_time(self, actual_session):
        return actual_session.session_date_time

    def get_session_name(self, actual_session):
        activity_type = actual_session.activity_type
        planned_session = None
        event_date = False
        session_date_time = actual_session.session_date_time
        session_date = session_date_time.date()

        if self.context["pro_feature_access"] and not self.context["user_away"]:
            planned_session = actual_session.get_planned_session_from_list(
                self.context["planned_sessions"]
            )

            event_date = True if session_date in self.context["event_dates"] else False

        return get_session_name(
            actual_session,
            planned_session,
            session_date_time,
            event_date,
            activity_type,
        )

    def get_session_edit_options(self, actual_session):
        return {"is_cancellable": False, "is_movable": False, "movable_days": []}

    def get_session_timespan(self, actual_session):
        return round(actual_session.actual_duration * 60)

    def get_session_score(self, actual_session):
        if not (actual_session.actual_duration and self.context["pro_feature_access"]):
            return None
        session_score = actual_session.session_score
        return session_score.get_overall_score() if session_score else None

    def get_session_accuracy_score(self, actual_session):
        if not (actual_session.actual_duration and self.context["pro_feature_access"]):
            return None
        session_score = actual_session.session_score
        return session_score.get_overall_accuracy_score() if session_score else None

    def get_session_pss(self, actual_session):
        return round(actual_session.actual_pss)

    def get_session_distance(self, actual_session):
        actual_distance = actual_session.actual_distance_in_meters / 1000  # meter to Km
        distance = str(round(actual_distance, 1))
        return distance + " km"

    def get_session_elevation(self, actual_session):
        elevation = str(round(actual_session.elevation_gain, 0))
        return elevation + " m"

    def get_zone_focus(self, actual_session):
        if self.context["pro_feature_access"] and not self.context["user_away"]:
            planned_session = actual_session.get_planned_session_from_list(
                self.context["planned_sessions"]
            )
            if planned_session:
                return planned_session.zone_focus

    def get_third_party_code(self, actual_session):
        return actual_session.third_party.code

    def get_planned_session_name(self, actual_session):
        if self.context["pro_feature_access"] and not self.context["user_away"]:
            planned_session = actual_session.get_planned_session_from_list(
                self.context["planned_sessions"]
            )

            return planned_session.name if planned_session else None

    def get_show_pairing_option(self, actual_session):
        """
        Day is completed if it is a recovery day or an actual session is already paired with today's planned session.
        If there isn't any planned session for this date then also return true. If it's event day then ignore the
        recovery day. Don't show pairing option for basic subscription.
        """
        if not self.context["pro_feature_access"] or self.context["user_away"]:
            return False

        planned_session = (
            self.context["planned_sessions"]
            .filter(session_date_time__date=actual_session.session_date_time.date())
            .last()
        )

        if (
            planned_session
            and actual_session.activity_type == ActivityTypeEnum.CYCLING.value[1]
        ):
            return not (
                self.context["actual_sessions"]
                .filter(
                    session_code=planned_session.session_code,
                    is_active=True,
                    third_party__isnull=False,
                )
                .exists()
                or (
                    planned_session.is_recovery_session()
                    and actual_session.session_date_time.date()
                    not in self.context["event_dates"]
                )
            )
        return False

    def get_pairing_option_message(self, actual_session):
        if not self.context["pro_feature_access"] or self.context["user_away"]:
            return None

        planned_session = (
            self.context["planned_sessions"]
            .filter(session_date_time__date=actual_session.session_date_time.date())
            .last()
        )

        if not planned_session:
            return None

        actual_session_name = self.get_session_name(actual_session)
        is_event_session = False
        if actual_session.session_date_time.date() in self.context["event_dates"]:
            is_event_session = True
            planned_session_name = planned_session.user_plan.user_event.name
        else:
            planned_session_name = planned_session.name

        return SessionPairingMessage.get_pairing_option_message(
            actual_session_name, planned_session_name, is_event_session
        )


class PlannedSessionSerializer(serializers.ModelSerializer):
    session_metadata = serializers.SerializerMethodField()
    session_date_time = serializers.SerializerMethodField()
    session_name = serializers.SerializerMethodField()
    session_message = serializers.SerializerMethodField()
    session_edit_options = serializers.SerializerMethodField()
    session_timespan = serializers.SerializerMethodField()
    session_pss = serializers.SerializerMethodField()

    class Meta:
        model = PlannedSession
        fields = (
            "session_metadata",
            "session_date_time",
            "session_name",
            "session_message",
            "zone_focus",
            "session_edit_options",
            "session_timespan",
            "session_pss",
        )

    def get_session_metadata(self, planned_session):
        return {
            "planned_id": planned_session.id,
            "actual_id": None,
            "session_type": SessionTypeEnum.RECOVERY
            if planned_session.zone_focus == 0
            else SessionTypeEnum.CYCLING,
            "session_status": SessionStatusEnum.PLANNED,
            "session_label": SessionLabelEnum.PLANNED_SESSION,
        }

    def get_session_date_time(self, planned_session):
        return planned_session.session_date_time

    def get_session_name(self, planned_session):
        return planned_session.name

    def get_session_message(self, planned_session):
        if planned_session.zone_focus == 0:
            return CALENDAR_RECOVERY_TILE_MESSAGE

    def get_session(self, planned_sessions, day, today):
        session = planned_sessions.filter(day_code=day.day_code).first()
        if session:
            if (
                day.activity_date < today and not session.is_completed
            ):  # if past day session is not completed then it is a rest day
                return None
            else:
                return session
        else:
            return None

    def check_over_training(
        self, week, week_days_intensities, day, today, planned_sessions, movable_session
    ):
        consecutive_days = [day]
        total_intensity = movable_session.planned_intensity
        previous_day = day.previous_day
        while previous_day:
            if (
                previous_day.activity_date < week.start_date
                or previous_day == movable_session.day
            ):
                break
            previous_day_session = self.get_session(
                planned_sessions, previous_day, today
            )
            if previous_day and previous_day_session:
                consecutive_days.append(previous_day)
                if previous_day_session.is_completed:
                    total_intensity += (
                        previous_day_session.actual_session.actual_intensity
                    )
                else:
                    total_intensity += previous_day_session.planned_intensity
            else:
                break
            previous_day = previous_day.previous_day

        next_day = day.next_day
        while next_day:
            if (
                next_day.activity_date > week.end_date
                or next_day == movable_session.day
            ):
                break
            next_day_session = self.get_session(planned_sessions, next_day, today)
            if next_day and next_day_session:
                consecutive_days.append(next_day)
                total_intensity = total_intensity + next_day_session.planned_intensity
            else:
                break
            next_day = next_day.next_day

        # high intensity condition
        high_intensity_days = False
        intensities = week_days_intensities
        day_no = day.activity_date.weekday()
        intensities[day_no] = intensities[movable_session.day.activity_date.weekday()]
        intensities[movable_session.day.activity_date.weekday()] = 0
        if day_no + 1 <= 6 and day_no + 2 <= 6 and not high_intensity_days:
            if (
                intensities[day_no] > MTI
                and intensities[day_no + 1] > MTI
                and intensities[day_no + 2] > MTI
            ):
                high_intensity_days = True
        if day_no + 1 <= 6 and day_no - 1 >= 0 and not high_intensity_days:
            if (
                intensities[day_no] > MTI
                and intensities[day_no + 1] > MTI
                and intensities[day_no - 1] > MTI
            ):
                high_intensity_days = True
        if day_no - 1 >= 0 and day_no - 2 >= 0 and not high_intensity_days:
            if (
                intensities[day_no] > MTI
                and intensities[day_no - 1] > MTI
                and intensities[day_no - 2] > MTI
            ):
                high_intensity_days = True

        if len(consecutive_days) > 3:
            return "RECOVERY"
        elif high_intensity_days:
            return "HIGH_INTENSITY"
        else:
            return None

    def get_movable_days(
        self,
        week,
        today,
        movable_session,
        session_movable_days,
        user_planned_sessions,
        current_week_planned_sessions,
        week_days_session_intensities,
    ):
        movable_days = []
        for day in session_movable_days:
            session = current_week_planned_sessions[day.day_code]
            if session and session.zone_focus == 0:
                over_training_message = self.check_over_training(
                    week,
                    week_days_session_intensities,
                    day,
                    today,
                    user_planned_sessions,
                    movable_session,
                )
                movable_days.append(
                    {
                        "day_id": day.id,
                        "date": day.activity_date,
                        "day_name": day.activity_date.strftime("%A"),
                        "over_training": over_training_message,
                    }
                )
        return movable_days

    def check_cancellable(self, user_session, week, today, is_completed_day):
        if (
            user_session.zone_focus != 0
            and is_completed_day is False
            and (today <= user_session.session_date_time.date() <= week.end_date)
        ):
            return True
        else:
            return False

    def check_movable(self, user_session, week, is_completed_day):
        if (
            user_session.zone_focus != 0
            and is_completed_day is False
            and (
                week.start_date
                <= user_session.session_date_time.date()
                <= week.end_date
            )
        ):
            return True
        else:
            return False

    def get_session_edit_options(self, user_session):
        week = self.context["current_week"]
        today = self.context["user_today"]
        session_is_movable = False
        session_is_cancellable = False
        movable_days = []

        is_completed_day = self.context["is_completed_day"]
        if week:
            if (
                week.start_date
                <= user_session.session_date_time.date()
                <= week.end_date
                and not user_session.is_recovery_session()
            ):
                session_is_cancellable = self.check_cancellable(
                    user_session, week, today, is_completed_day
                )
                session_is_movable = self.check_movable(
                    user_session, week, is_completed_day
                )
                if session_is_movable:
                    week_days_session_intensities = self.context[
                        "week_days_session_intensities"
                    ]
                    session_movable_days = self.context["session_movable_days"]
                    current_week_planned_sessions = self.context[
                        "current_week_planned_sessions"
                    ]
                    user_planned_sessions = self.context["user_planned_sessions"]
                    movable_days = self.get_movable_days(
                        week,
                        today,
                        user_session,
                        session_movable_days,
                        user_planned_sessions,
                        current_week_planned_sessions,
                        week_days_session_intensities,
                    )

        return {
            "is_cancellable": session_is_cancellable,
            "is_movable": session_is_movable,
            "movable_days": movable_days,
        }

    def get_session_timespan(self, planned_session):
        return int(planned_session.planned_duration * 60)

    def get_session_pss(self, planned_session):
        return round(planned_session.planned_pss)


class PlannedSessionCustomSerializer:
    def __init__(self, queryset, event_dates, user, user_events):
        self.queryset = queryset
        self.event_dates = event_dates
        self.user = user
        self.user_events = user_events
        self.data = self.serialize_data()

    def get_session_metadata(self, planned_session, user_event, session_date):
        if session_date in self.event_dates:
            event_type = user_event.event_type.type
            if event_type == EventTypeEnum.MULTI_DAY.value[0]:
                session_label_type = SessionLabelTypeEnum.MULTIDAY_EVENT.value
                session_label = SessionLabelEnum.MULTIDAY_EVENT.value
            else:
                session_label_type = SessionLabelTypeEnum.EVENT.value
                session_label = SessionLabelEnum.PLANNED_EVENT.value
            session_type = SessionTypeEnum.CYCLING.value
        else:
            session_label_type = SessionLabelTypeEnum.TRAINING_SESSION
            session_type = (
                SessionTypeEnum.RECOVERY.value
                if planned_session.zone_focus == 0
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
        if planned_session.session_date_time.date() in self.event_dates:
            return planned_session.user_plan.user_event.name
        return planned_session.name

    def get_session_message(self, planned_session):
        if planned_session.is_recovery_session():
            return CALENDAR_RECOVERY_TILE_MESSAGE

    def get_session_edit_options(self):
        return {"is_cancellable": False, "is_movable": False, "movable_days": []}

    def get_session_timespan(self, planned_session):
        return int(planned_session.planned_duration * 60)

    def get_session_pss(self, planned_session):
        return round(planned_session.planned_pss)

    def get_session_distance(self, planned_session, session_date):
        if session_date in self.event_dates:
            distance = str(
                round(planned_session.user_plan.user_event.distance_per_day, 1)
            )
            return distance + " km"

    def get_session_elevation(self, planned_session, session_date):
        if session_date in self.event_dates:
            elevation_gain = planned_session.user_plan.user_event.elevation_gain
            elevation = str(round(elevation_gain, 0)) if elevation_gain else "0"
            return elevation + " m"

    def get_serialized_planned_session_dict(
        self, planned_session, user_event, session_date
    ):
        from core.apps.session.services import SetsAndRepsService

        return {
            "session_metadata": self.get_session_metadata(
                planned_session, user_event, session_date
            ),
            "session_date_time": self.get_session_date_time(planned_session),
            "event_duration_in_days": user_event.event_duration_in_days
            if user_event
            else None,
            "event_start_date": user_event.start_date if user_event else None,
            "event_end_date": user_event.end_date if user_event else None,
            "session_name": self.get_session_name(planned_session),
            "session_message": self.get_session_message(planned_session),
            "zone_focus": planned_session.zone_focus,
            "session_timespan": self.get_session_timespan(planned_session),
            "session_edit_options": self.get_session_edit_options(),
            "session_distance": self.get_session_distance(
                planned_session, session_date
            ),
            "session_pss": self.get_session_pss(planned_session),
            "session_elevation": self.get_session_elevation(
                planned_session, session_date
            ),
            "show_pairing_option": False,
            "intervals": SetsAndRepsService(
                self.user,
                planned_session.session.code,
                planned_session.pad_time_in_seconds,
            ).get_session_sets_and_reps()
            if planned_session.zone_focus != 0
            else None,
        }

    def serialize_data(self):
        serialized_planned_sessions = []
        for planned_session in self.queryset:
            session_date = planned_session.session_date_time.date()
            user_event = self.user_events.filter(
                start_date__lte=session_date, end_date__gte=session_date, is_active=True
            ).last()
            serialized_planned_session = self.get_serialized_planned_session_dict(
                planned_session, user_event, session_date
            )
            serialized_planned_sessions.append(serialized_planned_session)

        return serialized_planned_sessions


class AwayTileSerializerClass:
    def __init__(self, user, away_day, away_interval):
        self.user = user
        self.away_day = away_day
        self.away_interval = away_interval

    def get_delete_away_message(self):
        away_date_format = DateFormat(self.away_day.away_date)
        message = I_AM_AWAY_TILE_DELETE_MESSAGE.format(
            away_date_format.format("jS F Y")
        )
        return message

    def get_delete_all_away_message(self):
        if not self.check_multiple_away_days():
            return ""
        start_date_format = DateFormat(self.away_interval.start_date)
        end_date_format = DateFormat(self.away_interval.end_date)
        message = I_AM_AWAY_TILE_DELETE_MESSAGE_PLURAL.format(
            start_date_format.format("jS F Y"), end_date_format.format("jS F Y")
        )
        return message

    def check_multiple_away_days(self):
        if self.away_interval.start_date < self.away_interval.end_date:
            return True
        return False

    def get_session_message(self):
        away_reason = ""
        if self.away_interval.reason:
            away_reason = " due to {0}".format(self.away_interval.reason)
        if self.check_multiple_away_days():
            start_date_format = DateFormat(self.away_interval.start_date)
            end_date_format = DateFormat(self.away_interval.end_date)
            message = I_AM_AWAY_TILE_MESSAGE_PLURAL.format(
                start_date_format.format("jS F Y"), end_date_format.format("jS F Y")
            )
        else:
            away_date_format = DateFormat(self.away_day.away_date)
            message = I_AM_AWAY_TILE_MESSAGE.format(away_date_format.format("jS F Y"))
        message += away_reason
        return message

    def get_data(self):
        return {
            "session_edit_options": {
                "is_cancellable": False,
                "is_movable": False,
                "delete_today": {
                    "visible": True,
                    "message": self.get_delete_away_message(),
                },
                "delete_all": {
                    "visible": self.check_multiple_away_days(),
                    "message": self.get_delete_all_away_message(),
                },
                "movable_days": [],
            },
            "session_metadata": {
                "session_type": SessionTypeEnum.I_AM_AWAY,
                "session_status": None,
                "planned_id": None,
                "actual_id": None,
                "session_label": SessionLabelEnum.I_AM_AWAY,
                "user_away_id": self.away_day.id,
            },
            "session_name": SessionNameEnum.AWAY_SESSION_NAME,
            "session_message": self.get_session_message(),
            "zone_focus": None,
            "sensor_data": {},
        }
