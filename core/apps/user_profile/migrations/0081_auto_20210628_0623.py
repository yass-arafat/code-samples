# Generated by Django 3.0 on 2021-06-28 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0080_auto_20210628_0621'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileimage',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='usertrainingavailability',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
    ]
