import json
import logging
from datetime import datetime

from django.db.models import Q

from core.apps.activities.utils import dakghor_get_athlete_activity
from core.apps.common.dictionary.training_zone_dictionary import (
    training_zone_truth_table_dict,
)
from core.apps.common.enums.activity_type import ActivityTypeEnum
from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.utils import (
    create_new_model_instance,
    get_max_heart_rate_from_age,
    get_ride_summary_v2,
    initialize_dict,
)
from core.apps.daily.serializers import (
    DayActualSessionSerializer,
    DayPlannedSessionSerializer,
)
from core.apps.daily.utils import is_day_completed
from core.apps.evaluation.session_evaluation.dictionary import get_accuracy_scores_dict
from core.apps.evaluation.session_evaluation.models import (
    SessionScoreCategoriesTruthTable,
)
from core.apps.evaluation.session_evaluation.utils import (
    get_actual_session,
    is_time_spent_in_zone,
)
from core.apps.event.services import get_user_event_dates

from ....enums.feedback_option_enum import FeedbackOption
from ....enums.session_pairing_message_enum import SessionPairingMessage
from ....models import ActualSession, PlannedSession
from ....utils import (
    ftp_fthr_details,
    get_actual_power_and_hr_zone_data,
    get_edit_manual_activity_data,
    get_event_day_planned_sessions,
    get_manual_activity_ride_summary,
    get_planned_power_and_hr_zone_data,
    get_planned_session_interval_data,
    get_session_local_time,
    get_session_metadata,
    get_session_name,
    get_session_warnings,
)
from .dictionary import get_session_details_dict_other_data, get_sessions_overview_dict
from .utils import get_activity_info_v2

logger = logging.getLogger(__name__)


class SessionService:
    @classmethod
    def get_upcoming_ride(cls, user_auth):
        """Returns next planned session that user needs to complete"""
        user_away_dates = list(
            user_auth.user_away_days.filter(
                user_auth=user_auth, is_active=True
            ).values_list("away_date", flat=True)
        )
        current_date = datetime.today()

        planned_sessions = (
            PlannedSession.objects.filter(
                user_auth=user_auth,
                is_active=True,
                session_date_time__date__gte=current_date,
            )
            .exclude(session_date_time__in=user_away_dates)
            .exclude(zone_focus=0)
        )

        # Need to include event day sessions too which are stored as recovery session (zone focus = 0)
        event_day_sessions = (
            get_event_day_planned_sessions(user_auth)
            .filter(session_date_time__date__gte=current_date)
            .exclude(session_date_time__in=user_away_dates)
        )
        planned_sessions |= event_day_sessions

        today_planned_sessions = planned_sessions.filter(
            session_date_time__date=current_date
        )
        today_completed_session_ids = [
            planned_session.id
            for planned_session in today_planned_sessions
            if planned_session.is_evaluation_done
        ]
        return (
            planned_sessions.exclude(id__in=today_completed_session_ids)
            .select_related("session_type")
            .order_by("session_date_time")
            .first()
        )

    @classmethod
    def get_previous_rides(cls, user_auth):
        """Returns last 3 sessions that user uploaded"""
        cycling_type = ActivityTypeEnum.CYCLING.value[1]
        return (
            ActualSession.objects.filter_actual_sessions(
                user_auth=user_auth,
                session_date_time__lte=datetime.today(),
                third_party_id__isnull=False,
            )
            .filter(
                Q(strava_data__activity_type=cycling_type)
                | Q(garmin_data__activity_type=cycling_type)
                | Q(pillar_data__activity_type=cycling_type)
            )
            .select_related("third_party")
            .order_by("-session_date_time")[:3]
        )

    @classmethod
    def get_sessions_overview(cls, user_auth):
        event_dates = list(
            user_auth.user_plans.filter(is_active=True).values_list(
                "end_date", flat=True
            )
        )
        context = {
            "user": user_auth,
            "event_dates": event_dates,
        }

        upcoming_ride = cls.get_upcoming_ride(user_auth)
        upcoming_rides_dict_list = (
            upcoming_ride
            and [DayPlannedSessionSerializer(upcoming_ride, context=context).data]
        ) or []

        previous_rides = cls.get_previous_rides(user_auth)
        past_rides_dict_list = (
            previous_rides
            and DayActualSessionSerializer(
                previous_rides, context=context, many=True
            ).data
        ) or []

        return get_sessions_overview_dict(
            upcoming_rides_dict_list, past_rides_dict_list
        )

    @staticmethod
    def save_session_feedback(
        actual_session, effort_level, session_followed_as_planned, reason, explanation
    ):
        actual_session = create_new_model_instance(actual_session)
        actual_session.show_feedback_popup = False
        actual_session.effort_level = effort_level
        actual_session.session_followed_as_planned = session_followed_as_planned
        actual_session.feedback_option_code = (
            FeedbackOption.get_feedback_option_code(reason) if reason else None
        )
        actual_session.feedback_explanation = explanation
        actual_session.save()

        return get_session_metadata(
            actual_session=actual_session, planned_id=actual_session.planned_session.id
        )


class SessionDetailService:
    @classmethod
    def get_warning_messages(cls, user_auth, actual_id):
        if not actual_id:
            return []
        actual_session = get_actual_session(user_auth, actual_id)
        if actual_session:
            return get_session_warnings(actual_session)

    @staticmethod
    def get_planned_session(user, planned_id):
        if not planned_id:
            return None

        planned_session = PlannedSession.objects.filter(pk=planned_id).last()
        if not planned_session.is_active:
            planned_session = user.planned_sessions.filter(
                session_code=planned_session.session_code, is_active=True
            ).last()
        return planned_session

    @staticmethod
    def get_pairing_option_message(user, actual_session, event_date):
        is_event_session = actual_session.session_date_time.date() == event_date
        if is_event_session:
            planned_session_name = (
                user.user_plans.filter(is_active=True).last().user_event.name
            )
        else:
            planned_session_name = (
                user.planned_sessions.filter(
                    is_active=True,
                    session_date_time__date=actual_session.session_date_time.date(),
                )
                .last()
                .name
            )
        return SessionPairingMessage.get_session_evaluation_pairing_option_message(
            planned_session_name, is_event_session
        )

    def get_session_details(self, user, planned_id, actual_id, pro_feature_access):
        planned_session = None
        if pro_feature_access:
            planned_session = self.get_planned_session(user, planned_id)
        actual_session = get_actual_session(user, actual_id)
        if not (planned_session or actual_session):
            logger.error("Session not found")
            return {}

        # If actual session details is called from notification or warning, planned id won't be available.
        # So we need to check if this actual session is already paired or not.
        # The reason this case is handled here instead of in notification or warning's session metadata is that
        # user might pair sessions after notification is fetched, then if he clicks the notification, planned id
        # won't be available there.
        if not planned_session and pro_feature_access:
            planned_session = actual_session.planned_session

        return self.get_session_details_data(
            user, planned_session, actual_session, pro_feature_access
        )

    def get_user_plan(self, actual_session, planned_session):
        return actual_session.user_plan if actual_session else planned_session.user_plan

    def get_session_details_data(
        self, user, planned_session, actual_session, pro_feature_access
    ):

        user_personalise_data = user.personalise_data.filter(is_active=True).last()
        cur_ftp = user_personalise_data.current_ftp
        cur_fthr = user_personalise_data.current_fthr
        max_heart_rate = user_personalise_data.max_heart_rate
        if not max_heart_rate:
            max_heart_rate = get_max_heart_rate_from_age(
                user_personalise_data.date_of_birth
            )
        accuracy_scores_dict = None

        # Initialize the detail values
        actual_time_in_power_zones_dict = initialize_dict(0, 8)
        actual_time_in_hr_zones_dict = initialize_dict(0, 7)
        planned_interval_data = []
        actual_interval_data = []
        activity_info = []
        planned_duration = None
        planned_intensity = None
        zone_name = None
        zone_focus = None
        session_description = None
        ride_summary_dict = None
        planned_time_in_power_zones_dict = []
        planned_time_in_hr_zones_dict = []
        show_pairing_option = False
        show_pairing_message = (
            actual_session.show_pairing_message if actual_session else None
        )
        effort_level = None
        activity_label = None
        edit_manual_activity_data = None
        activity_type = actual_session and actual_session.activity_type
        planned_session_name = None
        session_followed_as_planned = None
        show_feedback_popup = False
        feedback_reason = None

        session_metadata = get_session_metadata(actual_session, planned_session)
        session_date_time = get_session_local_time(
            actual_session, planned_session, user
        )
        event_dates_list = get_user_event_dates(user=user)
        event_date = True if session_date_time.date() in event_dates_list else False
        activity_name = get_session_name(
            actual_session,
            planned_session,
            session_date_time,
            event_date,
            activity_type,
        )

        accuracy_score_overview = {}
        key_zones = []
        key_zone_description = ""
        power_zone_performance = ""
        heart_rate_zone_performance = ""

        if planned_session and not planned_session.is_recovery_session():
            planned_interval_data = get_planned_session_interval_data(
                planned_session, cur_ftp, cur_fthr, max_heart_rate
            )
            zone_focus = planned_session.zone_focus
            zone_name = training_zone_truth_table_dict[zone_focus]["zone_name"]
            (
                planned_time_in_power_zones_dict,
                planned_time_in_hr_zones_dict,
            ) = get_planned_power_and_hr_zone_data(planned_session)
            session_description = planned_session.description
            planned_duration = int(
                planned_session.planned_duration * 60
            )  # Converted from minutes to seconds
            planned_intensity = int(
                planned_session.planned_intensity * 100
            )  # Converted into percentage value from decimal
            key_zones = json.loads(planned_session.session.key_zones)
            key_zone_description = planned_session.session.get_key_zone_description(
                key_zones
            )

        is_ftp_input_needed = False
        is_fthr_input_needed = False

        if actual_session:
            if actual_session.athlete_activity_code:
                athlete_activity = dakghor_get_athlete_activity(
                    actual_session.athlete_activity_code
                ).json()["data"]["athlete_activity"]
            else:
                athlete_activity = None

            actual_interval_data = actual_session.actual_intervals or []
            activity_info = get_activity_info_v2(
                actual_session, athlete_activity, user_personalise_data
            )

            if athlete_activity:
                if athlete_activity["time_in_power_zone"]:
                    actual_time_in_power_zones_dict = json.loads(
                        athlete_activity["time_in_power_zone"]
                    )
                    if is_time_spent_in_zone(actual_time_in_power_zones_dict):
                        is_ftp_input_needed = not bool(
                            cur_ftp or user_personalise_data.ftp_input_denied
                        )

                    for zone in actual_time_in_power_zones_dict:
                        zone["value"] = int(zone["value"])

                if athlete_activity["time_in_heart_rate_zone"]:
                    actual_time_in_hr_zones_dict = json.loads(
                        athlete_activity["time_in_heart_rate_zone"]
                    )
                    if is_time_spent_in_zone(actual_time_in_hr_zones_dict):
                        is_fthr_input_needed = not bool(
                            cur_fthr or user_personalise_data.fthr_input_denied
                        )

                    for zone in actual_time_in_hr_zones_dict:
                        zone["value"] = int(zone["value"])
                ride_summary_dict = get_ride_summary_v2(
                    athlete_activity["ride_summary"]
                )
            elif actual_session.third_party.code == ThirdPartySources.MANUAL.value[0]:
                manual_activity = actual_session.pillar_data
                if manual_activity.average_power:
                    is_ftp_input_needed = not bool(
                        cur_ftp or user_personalise_data.ftp_input_denied
                    )
                if manual_activity.average_heart_rate:
                    is_fthr_input_needed = not bool(
                        cur_fthr or user_personalise_data.fthr_input_denied
                    )

                ride_summary_dict = get_manual_activity_ride_summary(manual_activity)
                edit_manual_activity_data = get_edit_manual_activity_data(
                    actual_session
                )

            effort_level = actual_session.effort_level
            activity_label = actual_session.session_label  # Obsolete
            if actual_session.description:
                session_description = actual_session.description
            (
                actual_time_in_power_zones_dict,
                actual_time_in_hr_zones_dict,
            ) = get_actual_power_and_hr_zone_data(
                actual_session,
                actual_time_in_power_zones_dict,
                actual_time_in_hr_zones_dict,
            )

            # If an actual session is already paired with the planned session of current actual session's date,
            # then we don't need to show any pairing message or option. But if not already paired, then we should show
            # the pairing option always and the show pairing message the value of show_pairing_message is True.
            # Also don't show pairing option to basic user.
            if (
                is_day_completed(
                    actual_session.session_date_time.date(), user, event_date
                )
                or not pro_feature_access
            ):
                show_pairing_message = False
                show_pairing_option = False
            else:
                show_pairing_option = True

            if planned_session and not planned_session.is_recovery_session():
                session_score = actual_session.session_score
                if session_score:
                    accuracy_score_overview = self.get_accuracy_score_overview(
                        session_score
                    )
                    (
                        accuracy_scores_dict,
                        power_zone_performance,
                        heart_rate_zone_performance,
                    ) = self.get_accuracy_scores(
                        planned_session,
                        actual_session,
                        athlete_activity,
                        cur_ftp,
                        cur_fthr,
                        key_zones,
                    )
                show_feedback_popup = actual_session.show_feedback_popup
                session_followed_as_planned = actual_session.session_followed_as_planned
                if not session_followed_as_planned:
                    feedback_option_code = actual_session.feedback_option_code
                    if (
                        feedback_option_code
                        and feedback_option_code != FeedbackOption.OTHER.value[0]
                    ):
                        feedback_reason = FeedbackOption.get_feedback_text(
                            actual_session.feedback_option_code
                        )
                    else:
                        feedback_reason = actual_session.feedback_explanation
            else:
                today_planned_session = PlannedSession.objects.filter(
                    user_auth=user,
                    is_active=True,
                    session_date_time__date=actual_session.session_date_time.date(),
                ).last()
                if today_planned_session:
                    planned_session_name = today_planned_session.name

        (
            is_power_meter_available,
            is_ftp_available,
            is_fthr_available,
        ) = ftp_fthr_details(user_personalise_data, cur_ftp, cur_fthr)

        pairing_option_message = None
        if show_pairing_message:
            pairing_option_message = self.get_pairing_option_message(
                user, actual_session, event_date
            )

        session_details_dict = get_session_details_dict_other_data(
            evaluation_scores=None,
            actual_time_in_power_zones_dict=actual_time_in_power_zones_dict,
            actual_time_in_hr_zones_dict=actual_time_in_hr_zones_dict,
            planned_time_in_power_zones=planned_time_in_power_zones_dict,
            planned_time_in_hr_zones=planned_time_in_hr_zones_dict,
            ride_summary_dict=ride_summary_dict,
            zone_focus=zone_focus,
            is_ftp_available=is_ftp_available,
            zone_name=zone_name,
            is_fthr_available=is_fthr_available,
            activity_info=activity_info,
            is_ftp_input_needed=is_ftp_input_needed,
            is_fthr_input_needed=is_fthr_input_needed,
            planned_interval_data=planned_interval_data,
            actual_interval_data=actual_interval_data,
            session_metadata=session_metadata,
            session_date_time=session_date_time,
            session_name=activity_name,
            show_pairing_message=show_pairing_message,
            pairing_option_message=pairing_option_message,
            show_pairing_option=show_pairing_option,
            session_description=session_description,
            planned_duration=planned_duration,
            planned_intensity=planned_intensity,
            effort_level=effort_level,
            edit_manual_activity_data=edit_manual_activity_data,
            key_zones=key_zones,
            key_zone_description=key_zone_description,
            power_zone_performance=power_zone_performance,
            heart_rate_zone_performance=heart_rate_zone_performance,
            accuracy_score_overview=accuracy_score_overview,
            accuracy_scores=accuracy_scores_dict,
            activity_label=activity_label,
            planned_session_name=planned_session_name,
            show_feedback_popup=show_feedback_popup,
            session_followed_as_planned=session_followed_as_planned,
            feedback_reason=feedback_reason,
        )

        return session_details_dict

    @staticmethod
    def get_accuracy_scores(
        planned_session, actual_session, athlete_activity, cur_ftp, cur_fthr, key_zones
    ):
        from core.apps.evaluation.session_evaluation.utils import (
            get_accuracy_scores_comment,
            get_time_spent_in_zones,
            is_time_spent_in_zone,
        )

        actual_time_in_power_zone = (
            json.loads(athlete_activity["time_in_power_zone"])
            if athlete_activity
            else []
        )
        actual_time_in_heart_rate_zone = (
            json.loads(athlete_activity["time_in_heart_rate_zone"])
            if athlete_activity
            else []
        )

        actual_time_in_zone = []
        if actual_session.is_manual_activity():
            manual_activity = actual_session.pillar_data
            if manual_activity.average_power:
                planned_time_in_zone = json.loads(
                    planned_session.planned_time_in_power_zone
                )
            else:  # TODO: if manual_activity.average_heart_rate:
                planned_time_in_zone = json.loads(
                    planned_session.planned_time_in_hr_zone
                )
        else:
            if cur_ftp and is_time_spent_in_zone(actual_time_in_power_zone):
                actual_time_in_zone = actual_time_in_power_zone
                planned_time_in_zone = json.loads(
                    planned_session.planned_time_in_power_zone
                )
            elif cur_fthr and is_time_spent_in_zone(actual_time_in_heart_rate_zone):
                actual_time_in_zone = actual_time_in_heart_rate_zone
                planned_time_in_zone = json.loads(
                    planned_session.planned_time_in_hr_zone
                )
            else:
                if cur_ftp:
                    planned_time_in_zone = json.loads(
                        planned_session.planned_time_in_power_zone
                    )
                else:  # if cur_fthr
                    planned_time_in_zone = json.loads(
                        planned_session.planned_time_in_hr_zone
                    )

        key_zone_performance = (
            actual_session.session_score.get_key_zone_performance_comment(
                len(key_zones)
            )
        )
        if is_time_spent_in_zone(actual_time_in_power_zone):
            power_zone_performance = key_zone_performance
        else:
            power_zone_performance = (
                "There is no power data included in this activity "
                "so your time in power zone performance can not be evaluated."
            )
        if is_time_spent_in_zone(actual_time_in_heart_rate_zone):
            heart_rate_zone_performance = key_zone_performance
        else:
            heart_rate_zone_performance = (
                "There is no heart rate data included in this activity "
                "so your time in heart rate zone performance can not be evaluated."
            )

        (
            actual_time_in_key_zones,
            actual_time_in_non_key_zones,
        ) = get_time_spent_in_zones(actual_time_in_zone, key_zones)
        (
            planned_time_in_key_zones,
            planned_time_in_non_key_zones,
        ) = get_time_spent_in_zones(planned_time_in_zone, key_zones)
        session_scores_tt = SessionScoreCategoriesTruthTable.objects.all().order_by(
            "id"
        )
        accuracy_scores_comment = get_accuracy_scores_comment(
            actual_session, session_scores_tt
        )
        accuracy_scores_dict = get_accuracy_scores_dict(
            actual_session,
            planned_session,
            accuracy_scores_comment,
            actual_time_in_key_zones,
            actual_time_in_non_key_zones,
            planned_time_in_key_zones,
            planned_time_in_non_key_zones,
        )
        return accuracy_scores_dict, power_zone_performance, heart_rate_zone_performance

    @staticmethod
    def get_accuracy_score_overview(session_score):
        return {
            "overall_accuracy_score": session_score.get_overall_accuracy_score(),
            "comment": session_score.get_overall_accuracy_score_label(),
            "remarks": session_score.get_overall_accuracy_score_comment(),
        }
