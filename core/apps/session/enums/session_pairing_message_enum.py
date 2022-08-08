from enum import Enum


class SessionPairingMessage(Enum):
    SESSION_PAIRING_OPTION = (
        "Pairing with Planned Session",
        "Do you want your {actual_session_name} session to be evaluated against your planned "
        "{planned_session_name} session?",
    )
    EVENT_PAIRING_OPTION = (
        "Pairing with Planned Event",
        "Do you want your {actual_session_name} session to be "
        "paired with your planned {planned_session_name} event?",
    )

    SESSION_PAIRING_SUCCESSFUL = (
        "Sessions Paired Successfully",
        "Your {actual_session_name} ride has been successfully paired with your planned "
        "{planned_session_name} session.",
    )
    EVENT_PAIRING_SUCCESSFUL = (
        "Session Paired Successfully",
        "Your {actual_session_name} ride has been successfully "
        "paired with your planned {planned_session_name} event.",
    )

    SESSION_DETAILS_SESSION_PAIRING_OPTION = (
        "Do you want to pair this ride with your scheduled "
        "{planned_session_name} session?"
    )
    SESSION_DETAILS_EVENT_PAIRING_OPTION = (
        "Do you want to pair this ride with your scheduled "
        "{planned_session_name} event?"
    )

    @classmethod
    def get_pairing_successful_message(
        cls, actual_session_name, planned_session_name, is_event_session
    ):
        message = (
            is_event_session and cls.EVENT_PAIRING_SUCCESSFUL
        ) or cls.SESSION_PAIRING_SUCCESSFUL
        return {
            "title": message.value[0],
            "body": message.value[1].format(
                actual_session_name=actual_session_name,
                planned_session_name=planned_session_name,
            ),
        }

    @classmethod
    def get_pairing_option_message(
        cls, actual_session_name, planned_session_name, is_event_session
    ):
        message = (
            is_event_session and cls.EVENT_PAIRING_OPTION
        ) or cls.SESSION_PAIRING_OPTION
        return {
            "title": message.value[0],
            "body": message.value[1].format(
                actual_session_name=actual_session_name,
                planned_session_name=planned_session_name,
            ),
        }

    @classmethod
    def get_session_evaluation_pairing_option_message(
        cls, planned_session_name, is_event_session
    ):
        message = (
            is_event_session and cls.SESSION_DETAILS_EVENT_PAIRING_OPTION
        ) or cls.SESSION_DETAILS_SESSION_PAIRING_OPTION
        return message.value.format(planned_session_name=planned_session_name)
