# Generated by Django 3.0 on 2020-08-17 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0013_merge_20200804_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='userauthmodel',
            name='strava_refresh_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userauthmodel',
            name='strava_token_expires_at',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userauthmodel',
            name='strava_user_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
