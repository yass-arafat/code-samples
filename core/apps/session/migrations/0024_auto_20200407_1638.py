# Generated by Django 3.0 on 2020-04-07 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0023_auto_20200407_1635'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usersession',
            old_name='time_in_zones',
            new_name='actual_time_in_zones',
        ),
        migrations.AddField(
            model_name='usersession',
            name='planned_time_in_zones',
            field=models.TextField(null=True),
        ),
    ]
