# Generated by Django 3.0 on 2020-04-07 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0022_auto_20200405_1709'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usersession',
            old_name='duration_score',
            new_name='actual_duration_score',
        ),
        migrations.RenameField(
            model_name='usersession',
            old_name='pss_score',
            new_name='actual_pss_score',
        ),
        migrations.RenameField(
            model_name='usersession',
            old_name='sqs_session_score',
            new_name='actual_sqs_session_score',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z0',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z1',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z2',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z3',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z4',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z5',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z6',
        ),
        migrations.RemoveField(
            model_name='usersession',
            name='time_in_Z7',
        ),
        migrations.AddField(
            model_name='usersession',
            name='fitfile_name',
            field=models.CharField(max_length=55, null=True),
        ),
        migrations.AddField(
            model_name='usersession',
            name='planned_duration_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usersession',
            name='planned_pss_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usersession',
            name='planned_sqs_session_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usersession',
            name='time_in_zones',
            field=models.TextField(null=True),
        ),
    ]