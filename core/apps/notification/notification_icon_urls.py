from core.apps.common import messages
from core.apps.common.tp_common_utils import AliasDict

ICON_URL = "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/notification/icon/"
NOTIFICATION_ICON_URLS = AliasDict(
    {
        "GARMIN_ICON": ICON_URL + "garmin.png",
        "STRAVA_ICON": ICON_URL + "strava.png",
        "CYCLING_ACTIVITY": ICON_URL + "cycling.png",
        "RUNNING_ACTIVITY": ICON_URL + "running.png",
        "WALKING_ACTIVITY": ICON_URL + "walking.png",
        "SWIMMING_ACTIVITY": ICON_URL + "swimming.png",
        "STRENGTH_ACTIVITY": ICON_URL + "strength.png",
        "ROWING_ACTIVITY": ICON_URL + "rowing.png",
        "WELLBEING_ACTIVITY": ICON_URL + "wellbeing.png",
        "OTHER_ACTIVITY": ICON_URL + "other.png",
        "WEEK_ANALYSIS": ICON_URL + "weekly_activity_report.png",
        "WAHOO_ICON": ICON_URL + "wahoo.png",
        "PAYMENT_END_ICON": ICON_URL + "ic-end.png",
        "PAYMENT_SUCCESS_ICON": ICON_URL + "ic-payment.png",
        "TRIAL_EXPIRE_ICON": ICON_URL + "ic-timesup.png",
        "KNOWLEDGE_HUB_ICON": ICON_URL + "knowledge_hub.png",
        "ANCHOR_SESSION_ICON": ICON_URL + "cycling.png",
        "TRAINING_PROGRESS_UPDATE_ICON": ICON_URL + "cycling.png",
        "TRAINING_FILE_UPLOAD_CHECK": ICON_URL + "cycling.png",
        "RIDE_AND_RECORD_WEEK_ANALYSIS": ICON_URL + "weekly_activity_report.png",
        "FINAL_WEEK_ANALYSIS": ICON_URL + "weekly_activity_report.png",
        "PROVISIONAL_WEEK_ANALYSIS": ICON_URL + "weekly_activity_report.png",
        "PROVISIONAL_WEEK_ANALYSIS_UPDATE": ICON_URL + "weekly_activity_report.png",
        "ZWIFT_ICON": ICON_URL + "zwift.png",
        "SUUNTO_ICON": ICON_URL + "suunto.png",
    }
)

NOTIFICATION_ICON_URLS.add_aliases(
    [
        ("GARMIN_ICON", messages.GARMIN_LINKED_NOTIFICATION_TITLE),
        ("GARMIN_ICON", messages.GARMIN_DISCONNECT_NOTIFICATION_TITLE),
        ("STRAVA_ICON", messages.STRAVA_LINKED_NOTIFICATION_TITLE),
        ("STRAVA_ICON", messages.STRAVA_DISCONNECT_NOTIFICATION_TITLE),
        ("CYCLING_ACTIVITY", messages.HISTORIC_ACTIVITY_SYNC_NOTIFICATION_TITLE),
        ("CYCLING_ACTIVITY", messages.NEW_CYCLING_ACTIVITY_NOTIFICATION_TITLE),
        ("RUNNING_ACTIVITY", messages.NEW_RUNNING_ACTIVITY_NOTIFICATION_TITLE),
        ("WALKING_ACTIVITY", messages.NEW_WALKING_ACTIVITY_NOTIFICATION_TITLE),
        ("SWIMMING_ACTIVITY", messages.NEW_SWIMMING_ACTIVITY_NOTIFICATION_TITLE),
        ("STRENGTH_ACTIVITY", messages.NEW_STRENGTH_ACTIVITY_NOTIFICATION_TITLE),
        ("ROWING_ACTIVITY", messages.NEW_ROWING_ACTIVITY_NOTIFICATION_TITLE),
        ("WELLBEING_ACTIVITY", messages.NEW_WELLBEING_ACTIVITY_NOTIFICATION_TITLE),
        ("OTHER_ACTIVITY", messages.NEW_OTHER_ACTIVITY_NOTIFICATION_TITLE),
        ("WEEK_ANALYSIS", messages.WEEKLY_REPORT_NOTIFICATION_TITLE),
        ("WAHOO_ICON", messages.WAHOO_LINKED_NOTIFICATION_TITLE),
        ("WAHOO_ICON", messages.WAHOO_DISCONNECT_NOTIFICATION_TITLE),
        ("KNOWLEDGE_HUB_ICON", messages.KNOWLEDGE_HUB_NOTIFICATION_TITLE),
        ("PAYMENT_SUCCESS_ICON", messages.PAYMENT_INITIAL_SUCCESS_CAPTION),
        ("PAYMENT_SUCCESS_ICON", messages.PAYMENT_RENEWAL_SUCCESS_CAPTION),
        ("PAYMENT_END_ICON", messages.PAYMENT_CANCEL_SUCCESS_CAPTION),
        ("PAYMENT_END_ICON", messages.PAYMENT_EXPIRE_SUCCESS_CAPTION),
        ("TRIAL_EXPIRE_ICON", messages.TRIAL_EXPIRE_SUCCESS_CAPTION),
        ("ANCHOR_SESSION_ICON", messages.ANCHOR_SESSION_ADDED_NOTIFICATION_TITLE),
        (
            "TRAINING_PROGRESS_UPDATE_ICON",
            messages.TRAINING_PROGRESS_UPDATE_NOTIFICATION_TITLE,
        ),
        (
            "TRAINING_FILE_UPLOAD_CHECK",
            messages.TRAINING_FILE_UPLOAD_CHECK_NOTIFICATION_TITLE,
        ),
        (
            "RIDE_AND_RECORD_WEEK_ANALYSIS",
            messages.RIDE_AND_RECORD_WEEK_ANALYSIS_REPORT_NOTIFICATION_TITLE,
        ),
        ("FINAL_WEEK_ANALYSIS", messages.FINAL_WEEK_ANALYSIS_REPORT_NOTIFICATION_TITLE),
        (
            "PROVISIONAL_WEEK_ANALYSIS",
            messages.PROVISIONAL_WEEK_ANALYSIS_REPORT_NOTIFICATION_TITLE,
        ),
        (
            "PROVISIONAL_WEEK_ANALYSIS_UPDATE",
            messages.PROVISIONAL_WEEK_ANALYSIS_REPORT_UPDATE_NOTIFICATION_TITLE,
        ),
        (
            "ZWIFT_ICON",
            messages.ZWIFT_LINKED_NOTIFICATION_TITLE,
        ),
        (
            "ZWIFT_ICON",
            messages.ZWIFT_DISCONNECT_NOTIFICATION_TITLE,
        ),
        (
            "SUUNTO_ICON",
            messages.SUUNTO_LINKED_NOTIFICATION_TITLE,
        ),
        (
            "SUUNTO_ICON",
            messages.SUUNTO_DISCONNECT_NOTIFICATION_TITLE,
        ),
    ]
)
