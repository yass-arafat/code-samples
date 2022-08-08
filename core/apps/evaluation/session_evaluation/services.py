import logging

from core.apps.session.models import ActualSession, PlannedSession

from .utils import (
    get_session_details_graph_data_with_threshold,
    get_session_details_other_data,
)

logger = logging.getLogger(__name__)


class PlannedSessionEvaluation:
    @classmethod
    def get_session_graph_data_with_threshold(
        cls, user, planned_id, total_point, actual_id=None
    ):
        session_data_dict = get_session_details_graph_data_with_threshold(
            user, planned_id, total_point, actual_id
        )
        return session_data_dict

    @classmethod
    def get_session_graph_other_data(cls, user, planned_id, actual_id=None):
        planned_session = PlannedSession.objects.filter(
            pk=planned_id, user_auth=user, is_active=True
        ).last()
        actual_session = ActualSession.objects.filter(
            pk=actual_id, user_auth=user, is_active=True
        ).last()
        if not (planned_session or actual_session):
            session_data_dict = {}
            logger.error("session not found")
        else:
            session_data_dict = get_session_details_other_data(
                user, planned_session, actual_session
            )

        return session_data_dict
