# Generated by Django 3.0 on 2020-02-14 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0005_auto_20200212_2343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='session_type',
            field=models.IntegerField(blank=True, choices=[('M', 'Metric'), ('I', 'Imperial')], null=True),
        ),
    ]
