# Generated by Django 3.0 on 2020-04-08 22:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0026_usersession_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessionrules',
            name='session_type',
        ),
    ]