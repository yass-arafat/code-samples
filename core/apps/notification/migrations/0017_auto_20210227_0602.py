# Generated by Django 3.0 on 2021-02-27 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0016_auto_20210208_0526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pushnotificationlog',
            name='notification_type',
            field=models.CharField(choices=[('sync', 'Sync'), ('push_notification', 'Push Notification')], default='initiated', max_length=55),
        ),
    ]
