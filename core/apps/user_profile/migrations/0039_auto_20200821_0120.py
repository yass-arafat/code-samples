# Generated by Django 3.0 on 2020-08-20 19:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0038_auto_20200821_0051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useractivitytype',
            name='activity_name',
            field=models.CharField(max_length=255),
        ),
    ]