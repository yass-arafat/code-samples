# Generated by Django 3.0 on 2020-06-27 16:53

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0006_schedule_profile_data_update'),
        ('user_profile', '0021_userpersonalisedata_is_power_meter_available'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserActivityCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'User Activity Code TT',
                'db_table': 'user_activity_code',
            },
        ),
        migrations.CreateModel(
            name='UserActivityLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_code', models.PositiveSmallIntegerField(choices=[(1, 'Create Training Plan'), (2, 'Update Training Plan'), (3, 'User Email Login'), (4, 'User Logout'), (5, 'User Garmin Login'), (6, 'Garmin Deregistration'), (7, 'User Garmin Connect'), (8, 'User Garmin Disconnect'), (9, 'Forget Password'), (10, 'Reset Password'), (11, 'Email Confirmation'), (12, 'User Registration'), (13, 'Garmin Activity File Submission'), (14, 'Corrupt Garmin Activity File')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('request', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('response', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_auth', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_activity_logs', to='user_auth.UserAuthModel')),
            ],
            options={
                'verbose_name': 'User Activity Log',
                'db_table': 'user_activity_log',
            },
        ),
        migrations.AddIndex(
            model_name='useractivitylog',
            index=models.Index(fields=['activity_code'], name='user_activi_activit_3248d5_idx'),
        ),
        migrations.AddIndex(
            model_name='useractivitylog',
            index=models.Index(fields=['user_auth'], name='user_activi_user_au_573c79_idx'),
        ),
    ]
