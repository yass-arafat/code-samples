# Generated by Django 3.0 on 2020-05-09 09:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0016_auto_20200419_0217'),
        ('user_auth', '0006_schedule_profile_data_update'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userpersonalisedata',
            name='user_auth',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='user_auth',
        ),
        migrations.RemoveField(
            model_name='userscheduledata',
            name='user_auth',
        ),
    ]