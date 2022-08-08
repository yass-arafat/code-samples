# Generated by Django 3.0 on 2021-06-28 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0078_userprofile_access_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='useractivitylog',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='usermetadata',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='userpersonalisedata',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='zonedifficultylevel',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
    ]
