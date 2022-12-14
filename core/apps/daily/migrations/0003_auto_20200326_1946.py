# Generated by Django 3.0 on 2020-03-26 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0002_auto_20200326_2255'),
    ]

    operations = [
        migrations.RenameField(
            model_name='daily',
            old_name='actual_atl',
            new_name='actual_acute_load',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='actual_tsb',
            new_name='actual_freshness',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='actual_ctl',
            new_name='actual_load',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='max_atl',
            new_name='max_acute_load',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='max_tsb',
            new_name='max_freshness',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='max_ctl',
            new_name='max_load',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='planned_atl',
            new_name='planned_acute_load',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='planned_tsb',
            new_name='planned_freshness',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='planned_ctl',
            new_name='planned_load',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='target_atl',
            new_name='target_acute_load',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='target_tsb',
            new_name='target_freshness',
        ),
        migrations.RenameField(
            model_name='daily',
            old_name='target_ctl',
            new_name='target_load',
        ),
        migrations.AddField(
            model_name='daily',
            name='date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='daily',
            name='overall_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='daily',
            name='sqs_today',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
