# Generated by Django 3.2.5 on 2022-06-13 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0091_timezone_offset_second'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermetadata',
            name='cache_id',
            field=models.IntegerField(default=0),
        ),
    ]
