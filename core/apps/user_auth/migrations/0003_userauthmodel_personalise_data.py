# Generated by Django 3.0 on 2020-05-08 08:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0016_auto_20200419_0217'),
        ('user_auth', '0002_auto_20200330_0016'),
    ]

    operations = [
        migrations.AddField(
            model_name='userauthmodel',
            name='personalise_data',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user_profile.UserPersonaliseData'),
        ),
    ]
