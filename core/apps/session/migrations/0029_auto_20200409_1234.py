# Generated by Django 3.0 on 2020-04-09 06:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0028_sessiontype_rule'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessioninterval',
            name='session',
        ),
        migrations.AddField(
            model_name='session',
            name='session_interval',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='session.SessionInterval'),
        ),
    ]