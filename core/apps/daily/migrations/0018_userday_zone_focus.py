# Generated by Django 3.0 on 2020-04-05 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0017_auto_20200405_1609'),
    ]

    operations = [
        migrations.AddField(
            model_name='userday',
            name='zone_focus',
            field=models.IntegerField(default=0),
        ),
    ]
