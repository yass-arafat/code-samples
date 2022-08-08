# Generated by Django 3.0 on 2020-05-22 09:44

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garmin', '0002_auto_20200509_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='garmindata',
            name='created_at',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='garmindata',
            name='updated_at',
            field=models.DateField(auto_now=True),
        ),
    ]