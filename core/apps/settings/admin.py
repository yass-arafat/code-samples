from django.contrib import admin

from .models import ThirdPartySettings, UserSettings, UserSettingsQueue

admin.site.register([UserSettings, UserSettingsQueue, ThirdPartySettings])
