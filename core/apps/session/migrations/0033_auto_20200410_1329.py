# Generated by Django 3.0 on 2020-04-10 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0032_usersession_ride_summary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersession',
            name='actual_duration',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usersession',
            name='overall_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usersession',
            name='planned_duration',
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='usersession',
            name='prs_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usersession',
            name='sqs_today_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usersession',
            name='weighted_power',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='usersession',
            name='zone_focus',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
