# Generated by Django 3.0 on 2020-04-07 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0025_auto_20200407_2243'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersession',
            name='description',
            field=models.CharField(blank=True, help_text='User Session description', max_length=255, null=True),
        ),
    ]
