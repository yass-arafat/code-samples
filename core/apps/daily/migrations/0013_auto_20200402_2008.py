# Generated by Django 3.0 on 2020-04-02 20:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0012_auto_20200402_1840'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userday',
            old_name='week',
            new_name='user_week',
        ),
    ]
