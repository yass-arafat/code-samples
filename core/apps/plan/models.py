from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.apps.common.models import CommonFieldModel
from core.apps.plan.managers import UserPlanManager


class UserPlan(CommonFieldModel):
    plan_code = models.UUIDField(
        editable=False, null=True, help_text="Unique plan code for each plan"
    )
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="user_plans",
        null=True,
        on_delete=models.CASCADE,
    )
    user_id = models.UUIDField(null=True)
    user_event = models.ForeignKey(
        "event.UserEvent",
        related_name="user_plans",
        null=True,
        help_text=_("event of this plan"),
        on_delete=models.CASCADE,
    )
    user_package = models.ForeignKey(
        "packages.UserPackage",
        related_name="user_packages",
        null=True,
        help_text=_("Package for this plan"),
        on_delete=models.CASCADE,
    )
    start_date = models.DateField(
        blank=True, null=True, help_text=_("start date of the plan")
    )
    end_date = models.DateField(
        blank=True, null=True, help_text=_("end date of the plan")
    )
    target_load = models.FloatField(null=True, blank=True)
    target_acute_load = models.FloatField(null=True, blank=True)
    target_freshness = models.FloatField(null=True, blank=True)
    target_pss = models.FloatField(null=True, blank=True)
    actual_load = models.FloatField(
        null=True, blank=True, default=0.0, help_text="actual load of a user in plan"
    )
    actual_acute_load = models.FloatField(
        null=True,
        blank=True,
        default=0.0,
        help_text="actual acute load of a user in plan",
    )
    actual_freshness = models.FloatField(
        null=True,
        blank=True,
        default=0.0,
        help_text="actual freshness of a user in a plan",
    )
    actual_pss = models.FloatField(
        null=True, blank=True, default=0.0, help_text="actual pss of a user in plan"
    )
    event_target_load = models.FloatField(null=True, blank=True)
    event_target_freshness = models.FloatField(null=True, blank=True)
    time_in_Z0 = models.FloatField(null=True, blank=True)
    time_in_Z1 = models.FloatField(null=True, blank=True)
    time_in_Z2 = models.FloatField(null=True, blank=True)
    time_in_Z3 = models.FloatField(null=True, blank=True)
    time_in_Z4 = models.FloatField(null=True, blank=True)
    time_in_Z5 = models.FloatField(null=True, blank=True)
    time_in_Z6 = models.FloatField(null=True, blank=True)
    time_in_Z7 = models.FloatField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)

    objects = UserPlanManager()

    class Meta:
        db_table = "user_plan"
        verbose_name = "User Plan Table"

    def __str__(self):
        return "(" + str(self.id) + ") " + self.user_auth.email

    @property
    def user_goal(self):
        if self.user_event_id:
            return self.user_event
        if self.user_package_id:
            return self.user_package
        raise ValueError("User must have a goal connected to a plan")

    @property
    def total_days_in_plan(self):
        return (self.end_date - self.start_date).days

    def days_due_of_event(self, user_local_date):
        return (self.end_date - user_local_date).days
