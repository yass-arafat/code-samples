# Generated by Django 3.0 on 2020-08-05 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garmin', '0006_auto_20200802_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='garmindata',
            name='moving_fraction',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='moving fraction of an activity', max_digits=20),
        ),
    ]
