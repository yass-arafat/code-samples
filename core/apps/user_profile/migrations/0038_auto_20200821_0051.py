# Generated by Django 3.0 on 2020-08-20 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0037_auto_20200820_2044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useractivitylog',
            name='activity_code',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Create Training Plan'), (2, 'Update Training Plan'), (3, 'User Email Login'), (4, 'User Logout'), (5, 'User Garmin Login'), (6, 'Garmin Deregistration'), (7, 'User Garmin Connect'), (8, 'User Garmin Disconnect'), (9, 'Forget Password'), (10, 'Reset Password'), (11, 'Email Confirmation'), (12, 'User Registration'), (13, 'Garmin Activity File Submission'), (14, 'Corrupt Garmin Activity File'), (15, 'Ignored Garmin Activity File'), (16, 'Valid Garmin Activity File Calculation Successful'), (17, 'Valid Garmin Activity File Calculation Failed'), (18, 'Notification Creation'), (19, 'Notification History Creation'), (20, 'User Strava Connect'), (21, 'User Strava Disconnect'), (22, 'Valid Strava Activity Data Calculation Successful'), (23, 'Processed Garmin data and skipped session calculation'), (24, 'Processed Strava data and skipped session calculation')]),
        ),
    ]
