# Generated by Django 3.0 on 2021-03-23 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0077_actualsession_athlete_activity_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualsession',
            name='activity_type',
            field=models.CharField(max_length=55, null=True),
        ),
    ]