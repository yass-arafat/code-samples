# Generated by Django 3.0 on 2021-06-28 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0040_auto_20210602_0748'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualday',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='plannedday',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='userday',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
    ]
