# Generated by Django 3.0 on 2020-04-11 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0037_auto_20200411_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersessioninterval',
            name='fthr_percentage_lower',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='usersessioninterval',
            name='fthr_percentage_upper',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
