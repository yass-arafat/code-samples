# Generated by Django 3.0 on 2020-02-12 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0006_auto_20200212_2343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventtype',
            name='compete_approx_weekly_hrs',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='eventtype',
            name='podium_approx_weekly_hrs',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
