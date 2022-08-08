from django.db import models
from django.forms.models import model_to_dict

from ..common.models import CommonFieldModel
from .enums.distance_type_enum import DistanceTypeEnum
from .enums.event_sub_type_enum import EventSubTypeEnum
from .enums.event_type_enum import EventTypeEnum
from .enums.performance_goal_enum import PerformanceGoalEnum
from .enums.sports_type_enum import SportsTypeEnum


class EventDemandsTruthTable(models.Model):
    zone0_priority = models.IntegerField(blank=True, null=True, default=0)
    zone1_priority = models.IntegerField(blank=True, null=True, default=0)
    zone2_priority = models.IntegerField(blank=True, null=True, default=0)
    zone3_priority = models.IntegerField(blank=True, null=True, default=0)
    zone4_priority = models.IntegerField(blank=True, null=True, default=0)
    zone5_priority = models.IntegerField(blank=True, null=True, default=0)
    zone6_priority = models.IntegerField(blank=True, null=True, default=0)
    zone7_priority = models.IntegerField(blank=True, null=True, default=0)

    def get_zone_focuses(self):
        zone_focuses_dict = model_to_dict(
            self,
            fields=[field.name for field in self._meta.fields if field.name != "id"],
        )
        zone_focuses = dict(
            filter(lambda elem: elem[1] != 0, zone_focuses_dict.items())
        )
        sorted_zone_focuses = sorted(zone_focuses.items(), key=lambda x: x[1])
        return sorted_zone_focuses

    class Meta:
        db_table = "event_demands"
        verbose_name = "Event Demands Table"


class EventType(models.Model):
    ed_truth_table = models.ForeignKey(
        EventDemandsTruthTable,
        blank=True,
        null=True,
        related_name="event_types",
        on_delete=models.CASCADE,
    )
    details = models.ForeignKey(
        "event.EventTypeDetails",
        related_name="event_types",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    plan_name = models.CharField(max_length=55, null=True, blank=False)
    type = models.IntegerField(
        choices=[x.value for x in EventTypeEnum], null=True, blank=False
    )
    sub_type = models.IntegerField(
        choices=[x.value for x in EventSubTypeEnum], null=True, blank=False
    )
    distance_type = models.IntegerField(
        choices=[x.value for x in DistanceTypeEnum], null=True, blank=False
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "event_type"
        verbose_name = "Event Type Table"

    def __str__(self):
        event_type = EventTypeEnum.get_name(self.type)
        event_sub_type = EventSubTypeEnum.get_name(self.sub_type)
        event_distance_type = DistanceTypeEnum.get_name(self.distance_type)
        return f"({str(self.id)}) {event_type} {event_sub_type} {event_distance_type}"


class EventTypeDetails(models.Model):
    climbing_ratio = models.IntegerField(null=True, blank=True)
    minimum_distance = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    maximum_distance = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    minimum_elevation_gain = models.IntegerField(null=True, blank=True)
    maximum_elevation_gain = models.IntegerField(null=True, blank=True)
    complete_upper_target_prs = models.IntegerField(null=True, blank=True)
    complete_lower_target_prs = models.IntegerField(null=True, blank=True)
    compete_upper_target_prs = models.IntegerField(null=True, blank=True)
    compete_lower_target_prs = models.IntegerField(null=True, blank=True)
    podium_upper_target_prs = models.IntegerField(null=True, blank=True)
    podium_lower_target_prs = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "event_type_details"
        verbose_name = "Event Type Details Table"


class NamedEvent(models.Model):
    name = models.CharField(max_length=55)
    sub_name = models.CharField(max_length=255, null=True)
    description = models.TextField(
        blank=True, null=True, help_text="Description of the Named Event"
    )
    organiser = models.CharField(
        max_length=255, blank=True, null=True, help_text="Organiser of the Event"
    )
    city = models.CharField(
        max_length=255, null=True, help_text="City where the event will take place"
    )
    country = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Country where the events happening",
    )
    postcode = models.CharField(
        max_length=255, blank=True, null=True, help_text="Postcode of the country"
    )
    website_url = models.CharField(
        max_length=5000, blank=True, null=True, help_text="Website link of the event"
    )
    image_url = models.CharField(
        max_length=5000, blank=True, null=True, help_text="S3 link of the event image"
    )
    share_link = models.TextField(blank=True, null=True, help_text="Event share url")
    event_type = models.ForeignKey(
        "event.EventType",
        related_name="named_event",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )
    sports_type = models.CharField(
        max_length=55,
        choices=SportsTypeEnum.choices(),
        default=SportsTypeEnum.CYCLING.value,
        help_text="Refers to the type of sports of the event (e.g. Running, Cycling)",
    )
    distance_per_day = models.IntegerField(
        null=True, blank=True, verbose_name="Distance"
    )
    elevation_gain = models.IntegerField(null=True, blank=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    performance_goal = models.IntegerField(
        choices=[x.value for x in PerformanceGoalEnum]
    )
    climbing_ratio = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        db_table = "named_event"
        verbose_name = "Named Event Table"
        ordering = ["id"]

    def __str__(self):
        return f"({str(self.id)}) {self.name}"

    @property
    def event_duration_in_days(self):
        return (self.end_date - self.start_date).days + 1


class UserEvent(CommonFieldModel):
    name = models.CharField(max_length=55)
    event_type = models.ForeignKey(
        "event.EventType",
        related_name="user_events",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )
    sports_type = models.CharField(
        max_length=55,
        choices=SportsTypeEnum.choices(),
        default=SportsTypeEnum.CYCLING.value,
        help_text="Refers to the type of sports of the event (e.g. Running, Cycling)",
    )
    named_event_id = models.IntegerField(
        null=True, help_text="ID of the named event if a predefined event is selected"
    )
    distance_per_day = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    elevation_gain = models.IntegerField(null=True, blank=True)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    performance_goal = models.IntegerField(
        choices=[x.value for x in PerformanceGoalEnum], null=True, blank=False
    )
    user_auth = models.ForeignKey(
        "user_auth.UserAuthModel", related_name="user_events", on_delete=models.CASCADE
    )
    user_id = models.UUIDField(null=True)
    user_created_event_type = models.IntegerField(
        choices=[x.value for x in EventTypeEnum], null=True, blank=True
    )
    user_created_event_sub_type = models.IntegerField(
        choices=[x.value for x in EventSubTypeEnum], null=True, blank=True
    )
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "user_event"
        verbose_name = "User Event Table"

    def __str__(self):
        user_email = self.user_auth.email
        return f"({str(self.id)}) ({user_email}) {self.name}"

    @property
    def event_duration_in_days(self):
        return (self.end_date - self.start_date).days + 1
