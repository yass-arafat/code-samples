# Generated by Django 3.0 on 2020-10-21 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0004_stravadata_elevation_gain'),
    ]

    operations = [
        migrations.AddField(
            model_name='stravadata',
            name='is_flagged',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='stravadata',
            name='third_party_ride_summary',
            field=models.TextField(blank=True, help_text='User third party ride Summary', null=True),
        ),
    ]
