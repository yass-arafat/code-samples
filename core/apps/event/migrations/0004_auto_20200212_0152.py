# Generated by Django 3.0 on 2020-02-11 19:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0003_auto_20200212_0148'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userevent',
            old_name='user',
            new_name='user_auth',
        ),
    ]