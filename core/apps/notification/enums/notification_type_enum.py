from enum import Enum

from core.apps.notification.enums.push_notification_enums import (
    PushNotificationActionType,
)


class NotificationTypeEnum(Enum):
    AUTO_UPDATE_PLAN = (1, "Auto update training plan")
    GARMIN_ACTIVITY_UPLOAD = (2, "Garmin activity upload")
    NO_THIRD_PARTY_CONNECTED = (3, "No third party connected")
    RECOVERY_DAY = (4, "Recovery day")
    TODAY_SESSION = (5, "Today session")
    HIGH_SINGLE_RIDE_LOAD = (6, "High Single Ride Load")
    HIGH_RECENT_TRAINING_LOAD = (7, "High Recent Training Load")
    CONSECUTIVE_HIGH_INTENSITY_SESSIONS = (8, "Consecutive High Intensity Sessions")
    THIRD_PARTY_ACCOUNT_LINKED = (9, "Third party Account Linked")
    THIRD_PARTY_PROFILE_DISCONNECTED = (10, "Profile Disconnected")
    HISTORIC_ACTIVITY_SYNC = (11, "Historic Activity Synced")
    NEW_ACTIVITY = (12, "New Activity Sync")
    WEEK_ANALYSIS = (13, "Weekly Activity Report")
    KNOWLEDGE_HUB = (14, "Knowledge Hub")
    PAYMENT_INITIAL_SUCCESS = (15, "Initial Success Purchase")
    PAYMENT_RENEWAL_SUCCESS = (16, "Payment Renewal Success")
    PAYMENT_CANCEL_SUCCESS = (17, "Payment Cancellation Success")
    PAYMENT_EXPIRE_SUCCESS = (18, "Payment Expiration Success")
    TRIAL_EXPIRE_SUCCESS = (19, "Trial Period Expiration Success")
    ANCHOR_SESSION_ADDED = (20, "Anchor Session Added")
    TRAINING_PROGRESS_UPDATE = (21, "Training Progress Update")
    TRAINING_FILE_UPLOAD_CHECK = (22, "Training File Upload Check")
    RIDE_AND_RECORD_WEEK_ANALYSIS_REPORT = (23, "Ride and Record Week Analysis Report")
    FINAL_WEEK_ANALYSIS_REPORT = (24, "Final Week Analysis Report")
    PROVISIONAL_WEEK_ANALYSIS_REPORT = (25, "Provisional Week Analysis Report")
    PROVISIONAL_WEEK_ANALYSIS_REPORT_UPDATE = (
        26,
        "Provisional Week Analysis Report Update",
    )

    @classmethod
    def notification_panel_ids(cls):
        """These notifications are shown in notification panel, not in today focus panel"""
        return (
            cls.THIRD_PARTY_ACCOUNT_LINKED.value[0],
            cls.THIRD_PARTY_PROFILE_DISCONNECTED.value[0],
            cls.HISTORIC_ACTIVITY_SYNC.value[0],
            cls.NEW_ACTIVITY.value[0],
            cls.WEEK_ANALYSIS.value[0],
            cls.PAYMENT_INITIAL_SUCCESS.value[0],
            cls.PAYMENT_RENEWAL_SUCCESS.value[0],
            cls.PAYMENT_CANCEL_SUCCESS.value[0],
            cls.PAYMENT_EXPIRE_SUCCESS.value[0],
            cls.KNOWLEDGE_HUB.value[0],
            cls.TRIAL_EXPIRE_SUCCESS.value[0],
        )

    @classmethod
    def today_focus_panel_ids(cls):
        """These notifications are shown in today focus panel, not in notification panel"""
        return (
            cls.AUTO_UPDATE_PLAN.value[0],
            cls.GARMIN_ACTIVITY_UPLOAD.value[0],
            cls.RECOVERY_DAY.value[0],
            cls.NO_THIRD_PARTY_CONNECTED.value[0],
            cls.TODAY_SESSION.value[0],
            cls.HIGH_SINGLE_RIDE_LOAD.value[0],
            cls.HIGH_RECENT_TRAINING_LOAD.value[0],
            cls.CONSECUTIVE_HIGH_INTENSITY_SESSIONS.value[0],
        )

    @classmethod
    def push_notification_types(cls):
        return (cls.NEW_ACTIVITY.value[0],)

    @classmethod
    def get_push_notification_action_type(cls, notification_type):
        # TODO: refactor using loop instead of if-else
        if notification_type == cls.NEW_ACTIVITY.value[0]:
            return PushNotificationActionType.NEW_ACTIVITY.value
        elif notification_type == cls.PAYMENT_INITIAL_SUCCESS.value[0]:
            return PushNotificationActionType.PAYMENT_INITIAL_SUCCESS.value
        elif notification_type == cls.PAYMENT_RENEWAL_SUCCESS.value[0]:
            return PushNotificationActionType.PAYMENT_RENEWAL_SUCCESS.value
        elif notification_type == cls.PAYMENT_CANCEL_SUCCESS.value[0]:
            return PushNotificationActionType.PAYMENT_CANCEL_SUCCESS.value
        elif notification_type == cls.PAYMENT_EXPIRE_SUCCESS.value[0]:
            return PushNotificationActionType.PAYMENT_EXPIRE_SUCCESS.value
        elif notification_type == cls.TRIAL_EXPIRE_SUCCESS.value[0]:
            return PushNotificationActionType.TRIAL_EXPIRE_SUCCESS.value

    @classmethod
    def get_notification_type_enum_from_code(cls, notification_type_enum_code: int):
        for x in NotificationTypeEnum:
            if x.value[0] == notification_type_enum_code:
                return x
        raise ValueError(
            "{} is not a valid Enum code".format(notification_type_enum_code)
        )

    @classmethod
    def is_week_analysis_notification(cls, notification_type):
        return notification_type in (
            cls.RIDE_AND_RECORD_WEEK_ANALYSIS_REPORT.value[0],
            cls.FINAL_WEEK_ANALYSIS_REPORT.value[0],
            cls.PROVISIONAL_WEEK_ANALYSIS_REPORT.value[0],
            cls.PROVISIONAL_WEEK_ANALYSIS_REPORT_UPDATE.value[0],
        )

    @classmethod
    def is_button_type(cls, notification_type):
        return notification_type in (
            cls.TRAINING_FILE_UPLOAD_CHECK.value[0],
            cls.RIDE_AND_RECORD_WEEK_ANALYSIS_REPORT.value[0],
            cls.FINAL_WEEK_ANALYSIS_REPORT.value[0],
            cls.PROVISIONAL_WEEK_ANALYSIS_REPORT.value[0],
            cls.PROVISIONAL_WEEK_ANALYSIS_REPORT_UPDATE.value[0],
        )


class NotificationActionTypes(Enum):
    ROUTE = 0, "Route"
    URL = 1, "URL"
    UPDATE = 2, "Update"
