# Generated by Django 3.0 on 2020-03-07 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0002_auto_20200206_1240'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='actual_atl',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='actual_ctl',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='actual_pss',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='actual_tsb',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='event_target_ctl',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='event_target_tsb',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='target_atl',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='target_ctl',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='target_pss',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='target_tsb',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterModelTable(
            name='plan',
            table='user_plan',
        ),
    ]
