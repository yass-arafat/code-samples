# Generated by Django 3.0 on 2021-06-28 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0021_auto_20201019_1708'),
    ]

    operations = [
        migrations.AddField(
            model_name='userauthmodel',
            name='code',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='userauthmodel',
            name='user_id',
            field=models.UUIDField(editable=False, help_text='Unique user id for each every user', null=True),
        ),
    ]
