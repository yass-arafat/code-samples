# Generated by Django 3.0 on 2020-04-05 14:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0002_auto_20200330_0016'),
        ('user_profile', '0011_auto_20200405_1609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpersonalisedata',
            name='user_auth',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_personalise_data', to='user_auth.UserAuthModel'),
        ),
    ]
