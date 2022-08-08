import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PushNotificationMessages(Enum):
    NEW_ACTIVITY_TITLE = "New Cycling Activity \U0001F6B4"
    NEW_ACTIVITY_BODY = "Your new cycling activity is ready to view in Pillar."

    APP_UPDATE_TITLE = "New Update Available! 🎉"
    APP_UPDATE_BODY = (
        "A new Pillar App update is available. Click here to download "
        "the latest version."
    )

    WEEK_ANALYSIS_TITLE = "New Weekly Activity Report! 📊"
    WEEK_ANALYSIS_BODY = "Your weekly activity report is here, click to find out"

    RIDE_AND_RECORD_WEEK_ANALYSIS_TITLE = "Weekly Activity Report"
    RIDE_AND_RECORD_WEEK_ANALYSIS_BODY = (
        "Another week completed. Click to see your weekly report."
    )

    FINAL_WEEK_ANALYSIS_TITLE = "Weekly Activity Report"
    FINAL_WEEK_ANALYSIS_BODY = (
        "Another week completed. Click to see your weekly report and "
        "the adaptations for next week's training."
    )

    PROVISIONAL_WEEK_ANALYSIS_TITLE = "Provisional Weekly Activity Report"
    PROVISIONAL_WEEK_ANALYSIS_BODY = (
        "Just to let you know we’ve created a provisional weekly report and "
        "adaptations for next week's training. Don’t worry, when we receive any "
        "further ride uploads we will automatically update your weekly activity "
        "report and training plan."
    )

    PAYMENT_INITIAL_SUCCESS_TITLE = "Subscription Successful"
    PAYMENT_INITIAL_SUCCESS_BODY = (
        "Congrats! You are now a Pillar Premium member and can enjoy all our features."
    )

    PAYMENT_RENEWAL_SUCCESS_TITLE = "Subscription Renewal Successful"
    PAYMENT_RENEWAL_SUCCESS_BODY = (
        "Congrats! You Subscription has been renewal Successfully."
    )

    PAYMENT_CANCEL_SUCCESS_TITLE = "Subscription Cancelled"
    PAYMENT_CANCEL_SUCCESS_BODY = (
        "You will be a Pillar Basic member at the end of your billing period"
    )

    PAYMENT_EXPIRE_SUCCESS_TITLE = "Subscription Ended"
    PAYMENT_EXPIRE_SUCCESS_BODY = "You are now a Pillar basic member. You may upgrade anytime to access all premium features."

    TRIAL_EXPIRE_SUCCESS_TITLE = "Trial Period Expired"
    TRIAL_EXPIRE_SUCCESS_BODY = "You are now a Pillar Basic member. You may upgrade anytime to access all premium features."

    KNOWLEDGE_HUB_TITLE = "Knowledge Hub Tip"
    KNOWLEDGE_HUB_BODY = (
        "View information and tips about the {knowledge_hub_title} "
        "associated with your Hill Climb Training Pack."
    )


class PushNotificationActionType(Enum):
    NEW_ACTIVITY = "NEW_ACTIVITY"
    APP_UPDATE = "APP_UPDATE"
    WEEK_ANALYSIS = "WEEK_ANALYSIS"
    RIDE_AND_RECORD_WEEK_ANALYSIS = "RIDE_AND_RECORD_WEEK_ANALYSIS"
    FINAL_WEEK_ANALYSIS = "FINAL_WEEK_ANALYSIS"
    PROVISIONAL_WEEK_ANALYSIS = "PROVISIONAL_WEEK_ANALYSIS"
    KNOWLEDGE_HUB = "KNOWLEDGE_HUB"
    PAYMENT_INITIAL_SUCCESS = "PAYMENT_INITIAL_SUCCESS"
    PAYMENT_RENEWAL_SUCCESS = "PAYMENT_RENEWAL_SUCCESS"
    PAYMENT_CANCEL_SUCCESS = "PAYMENT_CANCEL_SUCCESS"
    PAYMENT_EXPIRE_SUCCESS = "PAYMENT_EXPIRE_SUCCESS"
    TRIAL_EXPIRE_SUCCESS = "TRIAL_EXPIRE_SUCCESS"

    @classmethod
    def get_message(cls, action_type):
        # TODO: refactor using loop instead of if-else
        """Returns Push Notification title and body depending on action_type"""
        if action_type == cls.NEW_ACTIVITY.value:
            return (
                PushNotificationMessages.NEW_ACTIVITY_TITLE.value,
                PushNotificationMessages.NEW_ACTIVITY_BODY.value,
            )
        elif action_type == cls.PAYMENT_INITIAL_SUCCESS.value:
            return (
                PushNotificationMessages.PAYMENT_INITIAL_SUCCESS_TITLE.value,
                PushNotificationMessages.PAYMENT_INITIAL_SUCCESS_BODY.value,
            )
        elif action_type == cls.PAYMENT_RENEWAL_SUCCESS.value:
            return (
                PushNotificationMessages.PAYMENT_RENEWAL_SUCCESS_TITLE.value,
                PushNotificationMessages.PAYMENT_RENEWAL_SUCCESS_BODY.value,
            )
        elif action_type == cls.PAYMENT_CANCEL_SUCCESS.value:
            return (
                PushNotificationMessages.PAYMENT_CANCEL_SUCCESS_TITLE.value,
                PushNotificationMessages.PAYMENT_CANCEL_SUCCESS_BODY.value,
            )
        elif action_type == cls.PAYMENT_EXPIRE_SUCCESS.value:
            return (
                PushNotificationMessages.PAYMENT_EXPIRE_SUCCESS_TITLE.value,
                PushNotificationMessages.PAYMENT_EXPIRE_SUCCESS_BODY.value,
            )
        elif action_type == cls.TRIAL_EXPIRE_SUCCESS.value:
            return (
                PushNotificationMessages.TRIAL_EXPIRE_SUCCESS_TITLE.value,
                PushNotificationMessages.TRIAL_EXPIRE_SUCCESS_BODY.value,
            )
        elif action_type == cls.APP_UPDATE.value:
            return (
                PushNotificationMessages.APP_UPDATE_TITLE.value,
                PushNotificationMessages.APP_UPDATE_BODY.value,
            )
        elif action_type == cls.WEEK_ANALYSIS.value:
            return (
                PushNotificationMessages.WEEK_ANALYSIS_TITLE.value,
                PushNotificationMessages.WEEK_ANALYSIS_BODY.value,
            )
        elif action_type == cls.RIDE_AND_RECORD_WEEK_ANALYSIS.value:
            return (
                PushNotificationMessages.RIDE_AND_RECORD_WEEK_ANALYSIS_TITLE.value,
                PushNotificationMessages.RIDE_AND_RECORD_WEEK_ANALYSIS_BODY.value,
            )
        elif action_type == cls.FINAL_WEEK_ANALYSIS.value:
            return (
                PushNotificationMessages.FINAL_WEEK_ANALYSIS_TITLE.value,
                PushNotificationMessages.FINAL_WEEK_ANALYSIS_BODY.value,
            )
        elif action_type == cls.PROVISIONAL_WEEK_ANALYSIS.value:
            return (
                PushNotificationMessages.PROVISIONAL_WEEK_ANALYSIS_TITLE.value,
                PushNotificationMessages.PROVISIONAL_WEEK_ANALYSIS_BODY.value,
            )
        elif action_type == cls.KNOWLEDGE_HUB.value:
            return (
                PushNotificationMessages.KNOWLEDGE_HUB_TITLE.value,
                PushNotificationMessages.KNOWLEDGE_HUB_BODY.value,
            )

        logger.error(
            f"Undefined Push Notification action type. Action Type: {action_type}"
        )
        raise ValueError
