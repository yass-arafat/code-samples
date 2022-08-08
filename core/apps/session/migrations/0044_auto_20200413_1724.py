# Generated by Django 3.0 on 2020-04-13 17:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0043_auto_20200413_1605'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersession',
            name='session_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_sessions', to='session.SessionType'),
        ),
    ]