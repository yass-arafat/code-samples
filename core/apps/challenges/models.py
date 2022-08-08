from django.db import models
from django.utils import timezone

from core.apps.common.models import CommonFieldModel


class Challenge(CommonFieldModel):
    title = models.CharField(
        max_length=255, help_text="Title of the Challenge e.g. March Distance Challenge"
    )
    challenge_type = models.CharField(
        max_length=55, help_text="Indicates type of a particular challenge"
    )
    start_date = models.DateField(help_text="Start date of the challenge")
    end_date = models.DateField(help_text="End date of the challenge")
    unit = models.CharField(
        max_length=30,
        null=True,
        help_text="Unit of the required value of a challenge e.g. "
        "km for distance challenge",
    )
    target_value = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Target value for completing this challenge",
    )
    summary = models.TextField(
        blank=True,
        null=True,
        help_text="Summary target of the challenge, which will be shown "
        "in the take challenge tile under the challenge title",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of the challenge"
    )
    image_url = models.TextField(
        blank=True, null=True, help_text="Challenge background image url"
    )
    badge_url = models.TextField(blank=True, null=True, help_text="Challenge badge url")
    share_link = models.TextField(
        blank=True, null=True, help_text="Challenge share url"
    )

    class Meta:
        db_table = "challenge"
        verbose_name = "Challenge"


class UserChallenge(CommonFieldModel):
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel",
        related_name="user_challenge",
        on_delete=models.CASCADE,
    )
    user_id = models.UUIDField(null=True)
    challenge = models.ForeignKey(
        Challenge, related_name="user_challenge", on_delete=models.CASCADE
    )
    is_completed = models.BooleanField(
        default=False, help_text="Indicates if the challenge is completed or not"
    )
    start_date = models.DateField(
        default=timezone.now,
        help_text="The date when the user signed up for the challenge",
    )
    completion_date = models.DateField(
        null=True, help_text="The date when the user completed the challenge"
    )
    achieved_value = models.DecimalField(
        null=True,
        decimal_places=2,
        max_digits=20,
        default=0.00,
        help_text="Value achieved for this challenge up until now",
    )
    completion_message_shown = models.BooleanField(
        default=False,
        help_text="Indicates if the challenge completion"
        "message is already shown or not",
    )

    class Meta:
        db_table = "user_challenge"
        verbose_name = "User Challenge"
