# Generated by Django 3.2.5 on 2022-02-08 17:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0088_auto_20220201_1811'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profileimage',
            name='user_auth',
        ),
    ]
