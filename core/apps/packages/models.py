from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.common.models import CommonFieldModel
from core.apps.packages.enums import GoalTypeEnum


class Package(models.Model):
    name = models.CharField(max_length=55)
    purpose = models.CharField(
        max_length=105,
        blank=True,
        help_text="Purpose or the outcome of a specific package",
    )
    description = models.TextField(blank=True, null=True)
    caption = models.TextField(
        blank=True, help_text="For package sub package page caption"
    )
    duration = models.CharField(
        max_length=55,
        blank=True,
        null=True,
        help_text="Duration of the training package in text format",
    )
    title_image_url = models.TextField(
        blank=True, null=True, help_text="Training package title image url"
    )
    description_image_url = models.TextField(
        blank=True, null=True, help_text="Training package description image url"
    )
    share_link = models.TextField(
        blank=True, null=True, help_text="Training package share url"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")

    goal_type = models.CharField(
        max_length=55, choices=[x.value for x in GoalTypeEnum], null=True
    )
    knowledge_hub_title = models.TextField(
        blank=True, null=True, help_text="Base knowledge hub page title"
    )
    knowledge_hub_text = models.TextField(
        blank=True, null=True, help_text="Base knowledge hub page text"
    )
    goal_detail_knowledge_hub_text = models.TextField(
        blank=True, null=True, help_text="Goal detail page knowledge hub page text"
    )

    class Meta:
        db_table = "package"
        ordering = ["id"]

    def __str__(self):
        return f"({str(self.id)}) {self.name}"


class SubPackage(models.Model):
    name = models.CharField(max_length=55)
    purpose = models.CharField(
        max_length=255,
        blank=True,
        help_text="Purpose or the outcome of a specific package",
    )
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(
        blank=True, null=True, help_text="Duration of the sub package in days"
    )
    package = models.ForeignKey(
        Package, related_name="sub_packages", on_delete=models.CASCADE
    )
    icon_url = models.TextField(
        blank=True, null=True, help_text="Training package icon url"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    week_zone_focuses = models.TextField(null=True, blank=True)
    multiple_duration = models.BooleanField(
        default=False, verbose_name="Multiple duration"
    )

    class Meta:
        db_table = "sub_package"
        ordering = ["id"]

    def __str__(self):
        return f"({str(self.id)}) {self.name}"


class UserPackage(CommonFieldModel):
    user_id = models.UUIDField()
    sub_package = models.ForeignKey(
        SubPackage, related_name="user_packages", on_delete=models.DO_NOTHING
    )

    class Meta:
        db_table = "user_package"
        ordering = ["id"]

    def __str__(self):
        return f"({str(self.id)}) {self.package.name}"

    @property
    def package(self):
        return self.sub_package.package


class KnowledgeHub(models.Model):
    package = models.ForeignKey(
        Package, related_name="knowledge_hub", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=55)
    week_no = models.IntegerField(help_text="The week no. when this hub will be shown")
    content_url = models.TextField(
        help_text="URL for the main content of knowledge hub"
    )
    calendar_text = models.TextField(help_text="calendar tile text of knowledge hub")
    notification_text = models.TextField(help_text="notification text of knowledge hub")
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        db_table = "knowledge_hub"
        ordering = ["id"]

    def __str__(self):
        return f"({str(self.id)}) {self.title}"


class UserKnowledgeHub(CommonFieldModel):
    knowledge_hub = models.ForeignKey(
        KnowledgeHub, related_name="user_knowledge_hub", on_delete=models.CASCADE
    )
    user_id = models.UUIDField()
    user_plan = models.ForeignKey(
        "plan.UserPlan",
        related_name="user_knowledge_hub",
        on_delete=models.CASCADE,
        help_text=_("Plan related to this user knowledge hub entry"),
    )
    activation_date = models.DateField(
        help_text="The first date of the week with "
        "which this knowledge hub entry is "
        "associated with e.g when user will"
        "receive notification for this "
        "knowledge hub entry (weekly basis)"
    )

    class Meta:
        db_table = "user_knowledge_hub"
        ordering = ["id"]

    def __str__(self):
        return f"({str(self.id)}) {self.knowledge_hub.title}"
