# Generated by Django 3.0 on 2020-07-11 16:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0034_auto_20200711_2255'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userevent',
            name='date',
        ),
    ]
