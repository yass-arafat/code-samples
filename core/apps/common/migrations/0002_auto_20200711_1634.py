# Generated by Django 3.0 on 2020-07-11 16:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cronhistorylog',
            options={'verbose_name': 'Cron History Log'},
        ),
        migrations.AlterModelTable(
            name='cronhistorylog',
            table='cron_history_log',
        ),
    ]
