# Generated by Django 3.0 on 2020-04-01 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0010_auto_20200331_1847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userday',
            name='created_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userday',
            name='updated_on',
            field=models.DateField(blank=True, null=True),
        ),
    ]
