from django.contrib import admin

from .models import Challenge, UserChallenge

admin.site.register(
    [
        Challenge,
        UserChallenge,
    ]
)
