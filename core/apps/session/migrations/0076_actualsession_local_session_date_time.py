# Generated by Django 3.0 on 2021-02-13 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0075_actualsession_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualsession',
            name='local_session_date_time',
            field=models.DateTimeField(null=True),
        ),
    ]
