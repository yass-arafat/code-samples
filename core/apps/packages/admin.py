from django.contrib import admin

from .models import Package, SubPackage, UserPackage

admin.site.register(Package)
admin.site.register(SubPackage)
admin.site.register(UserPackage)
