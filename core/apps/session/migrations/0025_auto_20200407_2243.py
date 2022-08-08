# Generated by Django 3.0 on 2020-04-07 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0024_auto_20200407_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersession',
            name='actual_time_in_zones',
            field=models.TextField(blank=True, help_text='User actual time in zone 0-7', null=True),
        ),
        migrations.AlterField(
            model_name='usersession',
            name='planned_time_in_zones',
            field=models.TextField(blank=True, help_text='User planned time in zone 0-7', null=True),
        ),
    ]
