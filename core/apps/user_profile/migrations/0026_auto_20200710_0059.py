# Generated by Django 3.0 on 2020-07-09 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0025_timezone'),
    ]

    operations = [
        migrations.AddField(
            model_name='timezone',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='timezone',
            name='type',
            field=models.CharField(default='UTC', max_length=10),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='timezone_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
