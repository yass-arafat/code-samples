from django.contrib import admin

from .models import PersonalRecord, RecordLevel, RecordType

admin.site.register([PersonalRecord, RecordType, RecordLevel])
