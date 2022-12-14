# Generated by Django 3.0 on 2020-04-10 13:54

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0024_eventtype_details'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userevent',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userevent',
            name='distance_per_day',
            field=models.FloatField(default=0.0),
        ),
    ]
