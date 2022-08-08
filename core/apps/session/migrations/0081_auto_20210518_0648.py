# Generated by Django 3.0 on 2021-05-18 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0080_actualsession_actual_intervals'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualsession',
            name='reason',
            field=models.TextField(help_text='The reason of an actual session row being created', null=True),
        ),
        migrations.AlterField(
            model_name='actualsession',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Active'),
        ),
    ]