# Generated by Django 3.0 on 2020-12-04 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0009_auto_20201204_1434'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thirdpartysettings',
            name='code',
            field=models.IntegerField(choices=[(1, 'Garmin'), (2, 'Strava'), (3, 'Wahoo'), (4, 'Manual')], null=True),
        ),
    ]
