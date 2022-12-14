# Generated by Django 3.2.5 on 2021-10-27 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0020_alter_pushnotificationlog_user_actions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pushnotificationlog',
            name='notification_status',
            field=models.CharField(blank=True, choices=[('initiated', 'Initiated'), ('acknowledged', 'Acknowledged')], default='initiated', max_length=55, null=True),
        ),
        migrations.AlterField(
            model_name='pushnotificationlog',
            name='notification_type',
            field=models.CharField(choices=[('sync', 'Sync'), ('push_notification', 'Push Notification')], default='push_notification', max_length=55),
        ),
    ]
