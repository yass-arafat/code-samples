# Generated by Django 3.0 on 2020-07-14 09:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0008_auto_20200714_1549'),
    ]

    operations = [
        migrations.RunSQL("update user_auth set notification_setting_id = ns.id from user_notification_setting as ns"
                          + " where user_auth.id=ns.user_auth_id")
    ]