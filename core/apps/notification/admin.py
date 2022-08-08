from django.contrib import admin

from .models import Notification, NotificationHistory, NotificationType

admin.site.register([Notification, NotificationType, NotificationHistory])
