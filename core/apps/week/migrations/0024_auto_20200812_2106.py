# Generated by Django 3.0 on 2020-08-12 21:06

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('week', '0023_userweek_week_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userweek',
            name='week_code',
            field=models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique week code for each week', null=True, unique=True),
        ),
    ]
