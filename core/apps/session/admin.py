from django.contrib import admin

from . import models

admin.site.register(
    [
        models.Session,
        models.SessionType,
        models.PlannedSession,
        models.SessionRules,
        models.SessionInterval,
        models.ActualSession,
        models.UserAway,
        models.UserAwayInterval,
    ]
)
