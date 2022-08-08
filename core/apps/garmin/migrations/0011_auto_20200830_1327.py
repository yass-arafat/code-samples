# Generated by Django 3.0 on 2020-08-30 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garmin', '0010_merge_20200819_2003'),
    ]

    operations = [
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_distance',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second Distance data', null=True),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_elevation',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second Elevation data', null=True),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_latitude',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second Latitude data', null=True),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_left_leg_power',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second Left Leg Power data', null=True),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_longitude',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second Longitude data', null=True),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_right_leg_power',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second Right Leg Power data', null=True),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_temperature',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second Temperature data', null=True),
        ),
    ]
