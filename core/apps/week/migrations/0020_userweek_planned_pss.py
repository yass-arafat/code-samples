# Generated by Django 3.0 on 2020-04-16 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('week', '0019_auto_20200410_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='userweek',
            name='planned_pss',
            field=models.FloatField(blank=True, default=0.0, help_text='actual load of a user in week', null=True),
        ),
    ]