# Generated by Django 3.0 on 2021-07-07 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subpackage',
            name='week_zone_focuses',
            field=models.CharField(blank=True, max_length=110, null=True),
        ),
    ]
