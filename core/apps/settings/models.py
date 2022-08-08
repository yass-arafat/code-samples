from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.apps.common.enums.third_party_sources_enum import ThirdPartySources
from core.apps.common.models import CommonFieldModel


class UserSettings(CommonFieldModel):
    class SettingsType(models.IntegerChoices):
        SYSTEM = 1, "System settings"
        USER = 2, "User settings"

    code = models.SlugField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("code is a unique slug field of settings type"),
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    name = models.CharField(
        max_length=255, blank=True, null=True, help_text=_("name of settings")
    )
    reason = models.CharField(
        max_length=255, blank=True, null=True, help_text=_("reason for this settings")
    )
    status = models.BooleanField(
        default=False,
        help_text=_("status indicates if this user settings is true or false"),
    )
    type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=SettingsType.choices,
        default=SettingsType.SYSTEM,
        help_text=_("settings type may be of system settings or user settings"),
    )
    updated_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("by whom this settings value is updated"),
    )
    # user_auth = models.ForeignKey(
    #     "user_auth.UserAuthModel",
    #     related_name="user_settings",
    #     on_delete=models.CASCADE,
    # )
    user_id = models.UUIDField(null=True)

    class Meta:
        verbose_name = "User Settings Table"
        indexes = [models.Index(fields=["code"])]

    def __str__(self):
        return "(" + str(self.pk) + ") " + self.user.email


class UserSettingsQueue(models.Model):
    class SettingsType(models.IntegerChoices):
        SYSTEM = 1, "System settings"
        USER = 2, "User settings"

    class QueueTaskStatus(models.IntegerChoices):
        PENDING = 1, "Pending"
        COMPLETED = 2, "Completed"

    active_from = models.DateTimeField(
        blank=True, null=True, help_text=_("from the time this settings will activate")
    )
    code = models.SlugField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("code is a unique slug field of settings type"),
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True, help_text=_("indicated if this raw is active or not")
    )
    name = models.CharField(
        max_length=255, blank=True, null=True, help_text=_("name of settings")
    )
    reason = models.CharField(
        max_length=255, blank=True, null=True, help_text=_("reason for this settings")
    )
    setting_status = models.BooleanField(
        default=False,
        help_text=_("status indicates if this user settings is true or false"),
    )
    task_priority = models.IntegerField(
        blank=True, null=True, default=0, help_text=_("priority of this task")
    )
    task_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=QueueTaskStatus.choices,
        default=QueueTaskStatus.PENDING,
        help_text=_("indicates if this task is completed or not from the queue"),
    )
    type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=SettingsType.choices,
        default=SettingsType.SYSTEM,
        help_text=_("settings type may be of system settings or user settings"),
    )
    updated_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("by whom this settings value is updated"),
    )
    user_id = models.UUIDField(null=True)

    class Meta:
        verbose_name = "User Settings Queue Table"
        indexes = [models.Index(fields=["code"])]

    def __str__(self):
        return "(" + str(self.pk) + ") " + self.user.email


class ThirdPartySettings(models.Model):
    name = models.CharField(
        max_length=55, unique=True, help_text="Third Party Service Name"
    )
    priority = models.PositiveSmallIntegerField(
        unique=True, null=False, help_text="Lower Priority will get Higher Precedence"
    )
    code = models.IntegerField(choices=[x.value for x in ThirdPartySources], null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "third_party_settings"
        verbose_name = "Third Party Service Settings"
