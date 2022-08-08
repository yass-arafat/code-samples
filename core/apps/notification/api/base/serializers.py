from rest_framework import serializers

from core.apps.common.date_time_utils import DateTimeUtils

from ...dictionary import (
    get_in_app_notification_action_dict,
    get_in_app_notification_button_action_dict,
)
from ...enums.notification_type_enum import NotificationTypeEnum
from ...models import InAppNotification, Notification, NotificationHistory
from ...notification_icon_urls import NOTIFICATION_ICON_URLS


class NotificationHistorySerializer(serializers.ModelSerializer):
    notification_id = serializers.SerializerMethodField()
    notification_title = serializers.SerializerMethodField()
    notification_body = serializers.SerializerMethodField()
    notification_time = serializers.SerializerMethodField()
    notification_type = serializers.SerializerMethodField()
    session_metadata = serializers.SerializerMethodField()

    class Meta:
        model = NotificationHistory
        fields = (
            "notification_id",
            "notification_title",
            "notification_body",
            "notification_time",
            "notification_type",
            "session_metadata",
        )

    def get_notification_id(self, notification_history):
        return notification_history.notification.id

    def get_notification_title(self, notification_history):
        return notification_history.notification.title

    def get_notification_body(self, notification_history):
        return notification_history.notification.message

    def get_notification_type(self, notification_history):
        return notification_history.notification.notification_type_id

    def get_notification_time(self, notification_history):
        offset = self.context["offset"]
        return DateTimeUtils.get_user_local_date_time_from_utc(
            offset, notification_history.notification.created_at
        )

    def get_session_metadata(self, notification_history):
        from core.apps.session.models import ActualSession
        from core.apps.session.utils import get_session_metadata

        notification_data = notification_history.notification.data
        actual_session = (
            ActualSession.objects.filter(code=notification_data, is_active=True).last()
            if notification_data
            else None
        )
        if not actual_session:
            return None
        return get_session_metadata(actual_session)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class InAppNotificationSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    notification_action = serializers.SerializerMethodField()
    is_button_type = serializers.SerializerMethodField()
    button_actions = serializers.SerializerMethodField()

    class Meta:
        model = InAppNotification
        fields = (
            "id",
            "title",
            "body",
            "icon",
            "time",
            "is_read",
            "is_button_type",
            "notification_action",
            "button_actions",
        )

    def get_icon(self, notification):
        icon = NOTIFICATION_ICON_URLS[notification.title]
        return icon

    def get_time(self, notification):
        return notification.created_at

    def is_read(self, notification):
        return notification.is_read()

    def get_notification_action(self, notification):
        notification_action = get_in_app_notification_action_dict(notification)
        return notification_action

    def get_is_button_type(self, notification):
        notification_type = notification.type
        return NotificationTypeEnum.is_button_type(notification_type)

    def get_button_actions(self, notification):
        button_actions = get_in_app_notification_button_action_dict(notification)
        return button_actions
