# Generated by Django 3.0 on 2020-08-11 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0031_auto_20200808_2358'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userday',
            old_name='date',
            new_name='activity_date',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='actual_freshness',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='actual_time_in_zones',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='is_completed',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='max_acute_load',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='max_freshness',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='max_pss',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='planned_freshness',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='planned_time_in_zones',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='type',
        ),
        migrations.AddField(
            model_name='userday',
            name='day_code',
            field=models.UUIDField(editable=False, help_text='Unique day code for each day', null=True),
        ),
        migrations.AddField(
            model_name='userday',
            name='reason',
            field=models.PositiveSmallIntegerField(choices=[('FIT_FILE_UPLOADED', 1), ('MORNING_CRONJOB', 2), ('MIDNIGHT_CRONJOB', 3)], null=True),
        ),
    ]