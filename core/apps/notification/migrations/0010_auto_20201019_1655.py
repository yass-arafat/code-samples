# Generated by Django 3.0 on 2020-10-19 16:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0009_usernotificationsetting_user_auth'),
    ]

    operations = [
        migrations.RunSQL(
            "update user_notification_setting as und set user_auth_id = ua.id"
            " from user_auth as ua"
            " where und.id = ua.notification_setting_id"
        )
    ]
