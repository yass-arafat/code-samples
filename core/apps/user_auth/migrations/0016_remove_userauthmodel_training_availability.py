# Generated by Django 3.0 on 2020-08-31 22:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0015_userauthmodel_training_availability'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userauthmodel',
            name='training_availability',
        ),
    ]
