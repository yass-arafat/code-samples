import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


class UserBlock(models.Model):
    block_code = models.UUIDField(
        editable=False, null=True, help_text="Unique block code for each block"
    )
    plan_code = models.UUIDField(
        editable=False, null=True, help_text="Week under the plan"
    )
    user_plan = models.ForeignKey(
        "plan.UserPlan",
        related_name="user_blocks",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("plan of this block"),
    )
    number = models.IntegerField(help_text=_("block number"))
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="user_blocks",
        null=True,
        on_delete=models.CASCADE,
        help_text=_("User of this block"),
    )
    user_id = models.UUIDField(null=True)
    no_of_weeks = models.IntegerField(
        help_text=_("total number of weeks for this block")
    )
    start_date = models.DateField(
        blank=True, null=True, help_text=_("start date of this block")
    )
    end_date = models.DateField(
        blank=True, null=True, help_text=_("end date of this block")
    )
    target_load = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    target_acute_load = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    target_freshness = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    planned_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="planned pss of this block",
    )
    actual_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual load of a user in block",
    )
    actual_acute_load = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual acute load of a user in block",
    )
    actual_freshness = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual freshness of a user in a block",
    )
    actual_pss = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="actual pss of a user in block",
    )

    planned_time_in_zones = models.TextField(
        null=True, blank=True, help_text="User planned time in zone 0-7"
    )
    actual_time_in_zones = models.TextField(
        null=True, blank=True, help_text="User actual time in zone 0-7"
    )

    zone_focus = models.IntegerField(
        null=True, blank=True, default=0, help_text=_("zone focus value for this block")
    )

    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        db_table = "user_block"
        verbose_name = "User Block Table"

    def __str__(self):
        return f"({str(self.id)}) ({self.user_auth.email}) Block: {str(self.number)}"
