# Generated by Django 3.0 on 2020-03-28 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0006_auto_20200328_1646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='day',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
