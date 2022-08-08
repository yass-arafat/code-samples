# Generated by Django 3.0 on 2020-07-25 10:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_auth', '0012_auto_20200725_0952'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSettingsQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active_from', models.DateTimeField(blank=True, help_text='from the time this settings will activate', null=True)),
                ('code', models.SlugField(blank=True, help_text='code is a unique slug field of settings type', max_length=255, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True, help_text='indicated if this raw is active or not')),
                ('name', models.CharField(blank=True, help_text='name of settings', max_length=255, null=True)),
                ('reason', models.CharField(blank=True, help_text='reason for this settings', max_length=255, null=True)),
                ('setting_status', models.BooleanField(default=False, help_text='status indicates if this user settings is true or false')),
                ('task_priority', models.IntegerField(blank=True, default=0, help_text='priority of this task', null=True)),
                ('task_status', models.CharField(blank=True, choices=[('SYSTEM', 'System settings'), ('USER', 'User settings')], default='SYSTEM', help_text='indicates if this task is completed or not from the queue', max_length=255, null=True)),
                ('type', models.CharField(blank=True, choices=[('SYSTEM', 'System settings'), ('USER', 'User settings')], default='SYSTEM', help_text='settings type may be of system settings or user settings', max_length=255, null=True)),
                ('updated_by', models.CharField(blank=True, help_text='by whome this settings value is updated', max_length=255, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_settings_queues', to='user_auth.UserAuthModel')),
            ],
            options={
                'verbose_name': 'User Settings Queue Table',
            },
        ),
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(blank=True, help_text='code is a unique slug field of settings type', max_length=255, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True, help_text='indicated if this raw is active or not')),
                ('name', models.CharField(blank=True, help_text='name of settings', max_length=255, null=True)),
                ('reason', models.CharField(blank=True, help_text='reason for this settings', max_length=255, null=True)),
                ('status', models.BooleanField(default=False, help_text='status indicates if this user settings is true or false')),
                ('type', models.CharField(blank=True, choices=[('SYSTEM', 'System settings'), ('USER', 'User settings')], default='SYSTEM', help_text='settings type may be of system settings or user settings', max_length=255, null=True)),
                ('updated_by', models.CharField(blank=True, help_text='by whome this settings value is updated', max_length=255, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_settings', to='user_auth.UserAuthModel')),
            ],
            options={
                'verbose_name': 'User Settings Table',
            },
        ),
    ]
