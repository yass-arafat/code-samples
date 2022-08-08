# Generated by Django 3.0 on 2020-05-13 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0016_auto_20200419_0217'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpersonalisedata',
            name='max_heart_rate',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='allow_notification',
            field=models.BooleanField(default=False),
        ),
    ]