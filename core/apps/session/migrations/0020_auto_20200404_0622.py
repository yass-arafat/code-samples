# Generated by Django 3.0 on 2020-04-04 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0019_auto_20200402_2154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessioninterval',
            name='name',
            field=models.CharField(default='N', max_length=55),
        ),
    ]