# Generated by Django 3.0 on 2020-03-13 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0005_auto_20200215_0301'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='unit',
            new_name='unit_system',
        )
    ]
