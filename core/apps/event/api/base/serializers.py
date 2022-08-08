from rest_framework import serializers

from core.apps.plan.utils import is_previous_goal_completed

from ...models import EventType, NamedEvent


class NamedEventSerializer(serializers.ModelSerializer):
    event_date = serializers.SerializerMethodField()
    event_distance = serializers.SerializerMethodField()
    event_elevation = serializers.SerializerMethodField()
    venue = serializers.SerializerMethodField()
    previous_goal_completed = serializers.SerializerMethodField()

    class Meta:
        model = NamedEvent
        fields = (
            "id",
            "name",
            "event_date",
            "event_duration_in_days",
            "event_type",
            "distance_per_day",  # deprecated from R12
            "event_distance",
            "event_elevation",  # deprecated from R12
            "elevation_gain",
            "performance_goal",
            "climbing_ratio",
            "description",
            "venue",
            "image_url",
            "share_link",
            "previous_goal_completed",
        )

    def get_previous_goal_completed(self, named_event):
        return is_previous_goal_completed(self.context["user"])

    def get_event_date(self, named_event):
        return named_event.start_date

    @staticmethod
    def get_event_distance(named_event):
        return f"{round(named_event.distance_per_day)} km Ride"

    @staticmethod
    def get_event_elevation(named_event):
        return f"{round(named_event.elevation_gain)} m"

    @staticmethod
    def get_venue(named_event):
        return (
            f"{named_event.city}, {named_event.country}"
            if named_event.city and named_event.country
            else None
        )


class EventNameSerializer(serializers.ModelSerializer):
    event_distance = serializers.SerializerMethodField()
    event_elevation = serializers.SerializerMethodField()
    event_date = serializers.SerializerMethodField()
    event_location = serializers.SerializerMethodField()

    class Meta:
        model = NamedEvent
        fields = (
            "id",
            "name",
            "image_url",
            "event_location",
            "event_date",
            "event_duration_in_days",
            "event_distance",
            "event_elevation",
        )

    def get_event_date(self, named_event):
        return named_event.start_date

    @staticmethod
    def get_event_distance(named_event):
        return f"{round(named_event.distance_per_day)} km Ride"

    @staticmethod
    def get_event_elevation(named_event):
        return f"{round(named_event.elevation_gain)} m"

    @staticmethod
    def get_event_location(named_event):
        return (
            f"{named_event.city}, {named_event.country}"
            if named_event.city and named_event.country
            else None
        )


class EventTypeSerializer(serializers.ModelSerializer):
    event_type_name = serializers.SerializerMethodField()

    class Meta:
        model = EventType
        fields = (
            "id",
            "event_type_name",
        )

    @staticmethod
    def get_event_type_name(event_type):
        return event_type.plan_name
