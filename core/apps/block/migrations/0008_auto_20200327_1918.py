# Generated by Django 3.0 on 2020-03-27 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('block', '0007_auto_20200327_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userblock',
            name='no_of_weeks',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
