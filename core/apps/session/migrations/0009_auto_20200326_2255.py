# Generated by Django 3.0 on 2020-03-26 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0008_auto_20200310_1803'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sessioninterval',
            options={'verbose_name': 'Session Interval Table'},
        ),
        migrations.RenameField(
            model_name='session',
            old_name='actual_ctl',
            new_name='actual_acute_load',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z0',
            new_name='actual_intensity',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z1',
            new_name='actual_load',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z2',
            new_name='duration_score',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z3',
            new_name='overall_score',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z4',
            new_name='planned_acute_load',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z5',
            new_name='planned_intensity',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z6',
            new_name='planned_load',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='duration_in_Z7',
            new_name='prs_score',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='planned_ctl',
            new_name='pss_score',
        ),
        migrations.RemoveField(
            model_name='session',
            name='zone',
        ),
        migrations.AddField(
            model_name='session',
            name='is_data_uploaded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='session',
            name='sqs_session_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='sqs_today_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z0',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z1',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z2',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z3',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z4',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z5',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z6',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='time_in_Z7',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='weighted_power',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterModelTable(
            name='sessioninterval',
            table='session_interval',
        ),
    ]
