# Generated by Django 3.0 on 2020-04-02 20:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0014_auto_20200402_2005'),
    ]

    operations = [
        migrations.RenameField(
            model_name='session',
            old_name='session_type',
            new_name='session_typey',
        ),
        migrations.RenameField(
            model_name='usersession',
            old_name='day',
            new_name='user_day',
        ),
    ]
