from django.contrib import admin

from .models import ActualDay, PlannedDay

admin.site.register([PlannedDay, ActualDay])
