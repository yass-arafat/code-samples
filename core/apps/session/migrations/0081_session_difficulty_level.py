# Generated by Django 3.0 on 2021-04-07 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0080_session_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='difficulty_level',
            field=models.SmallIntegerField(null=True),
        ),
    ]
