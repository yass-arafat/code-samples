# Generated by Django 3.0 on 2020-10-10 04:07

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0020_auto_20201005_1751'),
        ('notification', '0006_auto_20200926_1455'),
    ]

    operations = [
        migrations.CreateModel(
            name='PushNotificationSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_id', models.CharField(choices=[('com.pillar.app', 'Pillar Core')], default='com.pillar.app', max_length=55)),
                ('token_type', models.CharField(choices=[('fcm', 'FCM')], default='fcm', max_length=10)),
                ('device_id', models.IntegerField()),
                ('device_token', models.CharField(max_length=55)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_auth', models.ForeignKey(help_text='User ID', on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserAuthModel')),
            ],
            options={
                'verbose_name': 'Push Notification Setting',
                'db_table': 'push_notification_setting',
            },
        ),
        migrations.CreateModel(
            name='PushNotificationLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('sync', 'Sync'), ('push_notification', 'Push Notification')], max_length=55)),
                ('notification_status', models.CharField(blank=True, choices=[('initiated', 'Initiated'), ('acknowledged', 'Acknowledged')], max_length=55, null=True)),
                ('user_actions', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_auth', models.ForeignKey(help_text='User ID', on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserAuthModel')),
            ],
            options={
                'verbose_name': 'Push Notification Log',
                'db_table': 'push_notification_log',
            },
        ),
    ]
