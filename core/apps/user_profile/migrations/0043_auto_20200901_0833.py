# Generated by Django 3.0 on 2020-09-01 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0042_usertrainingavailability_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usertrainingavailability',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='usertrainingavailability',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]