# Generated by Django 3.0 on 2021-06-28 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0017_auto_20210227_0602'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushnotificationlog',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='pushnotificationsetting',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='usernotificationsetting',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
    ]
