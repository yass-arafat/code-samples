# Generated by Django 3.0 on 2020-02-06 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0002_remove_session_training_zone'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='status',
            field=models.BooleanField(default=False),
        ),
    ]