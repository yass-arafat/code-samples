# Generated by Django 3.2.5 on 2021-08-05 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0082_auto_20210805_0532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useractivitylog',
            name='data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='useractivitylog',
            name='request',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='useractivitylog',
            name='response',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='usermetadata',
            name='device_info',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
