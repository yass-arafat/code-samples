# Generated by Django 3.2.5 on 2022-01-13 10:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0047_auto_20220112_0643'),
    ]

    operations = [
        migrations.RunSQL("UPDATE user_event SET start_date=end_date;")
    ]
