# Generated by Django 3.2.5 on 2021-09-03 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0004_rename_package_type_package_goal_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subpackage',
            name='duration',
            field=models.IntegerField(blank=True, help_text='Duration of the sub package in days', null=True),
        ),
    ]