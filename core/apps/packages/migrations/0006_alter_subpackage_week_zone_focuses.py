# Generated by Django 3.2.5 on 2021-09-20 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0005_alter_subpackage_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subpackage',
            name='week_zone_focuses',
            field=models.TextField(blank=True, null=True),
        ),
    ]
