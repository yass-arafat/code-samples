from django.contrib import admin

from .models import UserWeek, WeekRules

admin.site.register([UserWeek, WeekRules])
