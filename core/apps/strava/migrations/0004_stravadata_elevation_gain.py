# Generated by Django 3.0 on 2020-09-15 04:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0003_stravadata_second_by_second_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='stravadata',
            name='elevation_gain',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Elevation gain during an activity', max_digits=20),
        ),
    ]