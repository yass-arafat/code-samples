# Generated by Django 3.0 on 2020-07-16 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0003_merge_20200714_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationhistory',
            name='expired_at',
            field=models.DateTimeField(help_text='Notification expired date time', null=True),
        ),
    ]
