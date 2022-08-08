# Generated by Django 3.2.5 on 2021-10-25 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_alter_cronhistorylog_cron_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cronhistorylog',
            name='cron_code',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Midnight Calculation'), (2, 'Morning Calculation'), (3, 'Auto Update Training Plan'), (4, 'Update User Settings'), (5, 'Update Today Notification For User'), (6, 'Week Analysis Report'), (7, 'Knowledge Hub Tip')]),
        ),
    ]