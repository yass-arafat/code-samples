# Generated by Django 3.0 on 2020-04-04 05:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0014_auto_20200403_1909'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userday',
            name='target_acute_load',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='target_freshness',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='target_load',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='target_pss',
        ),
    ]