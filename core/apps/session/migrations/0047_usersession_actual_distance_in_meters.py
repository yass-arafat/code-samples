# Generated by Django 3.0 on 2020-04-22 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0046_auto_20200419_0217'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersession',
            name='actual_distance_in_meters',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
    ]