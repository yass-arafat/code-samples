# Generated by Django 3.0 on 2021-06-28 06:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0012_auto_20210309_0620'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usersettings',
            old_name='user',
            new_name='user_auth',
        ),
        migrations.RenameField(
            model_name='usersettingsqueue',
            old_name='user',
            new_name='user_auth',
        ),
    ]