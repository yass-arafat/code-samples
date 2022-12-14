# Generated by Django 3.0 on 2020-08-02 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garmin', '0005_auto_20200628_0008'),
    ]

    operations = [
        migrations.RenameField(
            model_name='garmindata',
            old_name='second_hr_data',
            new_name='second_by_second_hr',
        ),
        migrations.RenameField(
            model_name='garmindata',
            old_name='second_power_data',
            new_name='second_by_second_power',
        ),
        migrations.AddField(
            model_name='garmindata',
            name='elapsed_time_in_seconds',
            field=models.IntegerField(default=0, help_text='Time where speed is 0 and power is 0'),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='moving_time_in_seconds',
            field=models.IntegerField(default=0, help_text='Time where speed is 0 and power is 0'),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='second_by_second_speed',
            field=models.TextField(blank=True, help_text='Activity Fit File Second by Second heart rate data', null=True),
        ),
    ]
