# Generated by Django 3.0 on 2021-01-18 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0014_auto_20201020_0550'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='data',
            field=models.TextField(blank=True, help_text='Holds data related to the notification e.g. actual session id for over-training notification', null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Active'),
        ),
    ]
