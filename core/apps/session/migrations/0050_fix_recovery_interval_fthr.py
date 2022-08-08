# Generated by Django 3.0 on 2020-05-22 18:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0049_session_interval_fthr_bound'),
    ]

    operations = [
        migrations.RunSQL(
            "update user_session_interval "
            "set fthr_percentage_upper = 0, fthr_percentage_lower = 0 "
            "where ftp_percentage_upper = 0 and ftp_percentage_lower = 0"
        )
    ]