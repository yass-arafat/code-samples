# Generated by Django 3.0 on 2020-09-08 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0002_auto_20200901_1441'),
    ]

    operations = [
        migrations.AddField(
            model_name='stravadata',
            name='second_by_second_time',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second elapsed time in seconds                                                              from start of the activity', null=True),
        ),
    ]
