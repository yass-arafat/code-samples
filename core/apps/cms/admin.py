from django.contrib import admin

from .models import InformationDetail, InformationSection

admin.site.register([InformationSection, InformationDetail])
