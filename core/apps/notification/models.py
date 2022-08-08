from django.db import models

from core.apps.common.const import DEFAULT_EXPIRE_TIME
from core.apps.common.models import CommonFieldModel


class Notification(CommonFieldModel):
    class RecipientType(models.IntegerChoices):
        USER_GROUP = 1, "User Group"
        INDIVIDUAL = 2, "Individual"
        ALL = 3, "All"

    title = models.CharField(
        max_length=55, blank=False, null=False, help_text="Title of user notification"
    )
    message = models.CharField(
        max_length=1000, null=False, help_text="Description of the notification"
    )
    recipient_type = models.PositiveSmallIntegerField(choices=RecipientType.choices)
    recipient_id = models.IntegerField(null=True, blank=True)
    initiator_name = models.CharField(
        max_length=55,
        null=False,
        help_text="Name of the notification initiator e.g. cron, admin",
    )
    initiator_id = models.IntegerField()
    notification_type = models.ForeignKey(
        "NotificationType",
        null=True,
        on_delete=models.SET_NULL,
        help_text="Type of the notification e.g. Campaign, Plan Update",
    )
    data = models.TextField(
        null=True,
        blank=True,
        help_text="Holds data related to the notification "
        "e.g. actual session code for over-training notification",
    )

    class Meta:
        db_table = "notification"
        verbose_name = "User Notification"


class NotificationType(models.Model):
    name = models.CharField(
        max_length=255, null=False, help_text="Name of the notification"
    )
    is_active = models.BooleanField(null=False, blank=False, default=True)
    priority = models.IntegerField(default=9999999)

    class Meta:
        db_table = "notification_type"
        verbose_name = "Notification Type"

    def __str__(self):
        return self.name


class NotificationHistory(models.Model):
    class NotificationActionType(models.IntegerChoices):
        INITIATED = 1, "Initiated"
        SHOWED = 2, "Showed"
        CLICKED = 3, "Clicked"
        SWIPED = 4, "Swiped"
        CLOSED = 5, "Closed"

    receiver = models.ForeignKey(
        "user_auth.UserAuthModel",
        null=True,
        on_delete=models.SET_NULL,
        help_text="Notification receiver User id",
    )
    user_id = models.UUIDField(null=True)
    notification = models.ForeignKey(
        "Notification",
        null=True,
        related_name="notification",
        on_delete=models.SET_NULL,
        help_text="Notification id",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(
        null=True, help_text="Notification expired date time"
    )
    action = models.PositiveIntegerField(choices=NotificationActionType.choices)

    class Meta:
        db_table = "notification_history"
        verbose_name = "Notification History"

    def is_read(self):
        return not bool(
            self.action
            in (
                self.NotificationActionType.INITIATED.value,
                self.NotificationActionType.SHOWED.value,
            )
        )


class UserNotificationSetting(CommonFieldModel):
    expired_time = models.TimeField(default=DEFAULT_EXPIRE_TIME)
    auto_closable = models.BooleanField(default=False)
    auto_closable_time = models.TimeField(null=True)
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="notification_setting",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_id = models.UUIDField(null=True)

    class Meta:
        db_table = "user_notification_setting"
        verbose_name = "User Notification Setting"


class PushNotificationSetting(models.Model):
    class TokenType(models.TextChoices):
        FCM = "fcm", "FCM"

    class AppId(models.TextChoices):
        CORE_APP = "com.pillar.app", "Pillar Core"

    # user_auth = models.ForeignKey(
    #     "user_auth.UserAuthModel", on_delete=models.CASCADE, help_text="User ID"
    # )
    user_id = models.UUIDField(null=True)

    app_id = models.CharField(
        max_length=55, choices=AppId.choices, default=AppId.CORE_APP
    )
    token_type = models.CharField(
        max_length=10, choices=TokenType.choices, default=TokenType.FCM
    )
    device_id = models.IntegerField()
    device_token = models.TextField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.device_id is None:
            user_last_setting = PushNotificationSetting.objects.filter(
                user_id=self.user_id
            ).last()
            self.device_id = user_last_setting.device_id + 1 if user_last_setting else 1

        super(PushNotificationSetting, self).save(*args, **kwargs)

    class Meta:
        db_table = "push_notification_setting"
        verbose_name = "Push Notification Setting"


class PushNotificationLog(models.Model):
    class NotificationType(models.TextChoices):
        SYNC = "sync", "Sync"
        PUSH_NOTIFICATION = "push_notification", "Push Notification"

    class NotificationStatus(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"

    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel", on_delete=models.CASCADE, help_text="User ID"
    )
    user_id = models.UUIDField(null=True)

    notification_type = models.CharField(
        max_length=55,
        choices=NotificationType.choices,
        default=NotificationType.PUSH_NOTIFICATION.value,
    )
    notification_status = models.CharField(
        max_length=55,
        choices=NotificationStatus.choices,
        null=True,
        blank=True,
        default=NotificationStatus.INITIATED.value,
    )

    user_actions = models.JSONField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "push_notification_log"
        verbose_name = "Push Notification Log"


class InAppNotification(models.Model):
    class NotificationActionType(models.IntegerChoices):
        INITIATED = 1, "Initiated"
        SHOWED = 2, "Showed"
        CLICKED = 3, "Clicked"
        SWIPED = 4, "Swiped"
        CLOSED = 5, "Closed"

    type = models.IntegerField(default=0)
    title = models.CharField(
        max_length=55, blank=False, null=False, help_text="title of the notification"
    )
    body = models.CharField(
        max_length=1000, null=False, help_text="description of the notification"
    )

    data = models.JSONField(
        null=True,
        blank=True,
        help_text="Holds data related to the notification "
        "e.g. actual session code for over-training notification",
    )

    action = models.PositiveIntegerField(
        choices=NotificationActionType.choices, default=NotificationActionType.INITIATED
    )
    receiver_id = models.UUIDField(
        null=True, editable=False, help_text="it referring to the user_id"
    )
    generated_by = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "in_app_notification"
        verbose_name = "In App Notification"

    def is_read(self):
        return not bool(
            self.action
            in (
                self.NotificationActionType.INITIATED.value,
                self.NotificationActionType.SHOWED.value,
            )
        )
