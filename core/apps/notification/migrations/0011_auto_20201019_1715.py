# Generated by Django 3.0 on 2020-10-19 17:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0021_auto_20201019_1708'),
        ('notification', '0010_auto_20201019_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usernotificationsetting',
            name='user_auth',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_setting', to='user_auth.UserAuthModel'),
        ),
    ]
