# Generated by Django 3.0 on 2020-08-11 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garmin', '0008_garmindata_second_by_second_cadence'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='garmindata',
            name='total_time_in_seconds',
        ),
        migrations.AddField(
            model_name='garmindata',
            name='ride_summary',
            field=models.TextField(blank=True, help_text='User ride Summary', null=True),
        ),
        migrations.AddField(
            model_name='garmindata',
            name='weighted_power',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
    ]
