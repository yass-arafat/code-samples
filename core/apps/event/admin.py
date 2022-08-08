from django.contrib import admin

from .models import (
    EventDemandsTruthTable,
    EventType,
    EventTypeDetails,
    NamedEvent,
    UserEvent,
)


@admin.register(NamedEvent)
class NamedEventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_date",
        "end_date",
        "event_type",
        "distance_per_day",
        "elevation_gain",
        "climbing_ratio",
        "is_active",
    )


admin.site.register([EventType, EventDemandsTruthTable, EventTypeDetails, UserEvent])
