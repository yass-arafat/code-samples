# Generated by Django 3.0 on 2020-04-08 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0021_auto_20200408_2244'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventdemandstruthtable',
            name='zone0_priority',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]