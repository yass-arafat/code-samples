# Generated by Django 3.0 on 2020-07-25 09:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0011_settings'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userauthmodel',
            name='third_party_connections',
        ),
        migrations.DeleteModel(
            name='Settings',
        ),
    ]
