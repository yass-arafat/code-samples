# Generated by Django 3.0 on 2020-09-23 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0045_auto_20200915_2131'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(choices=[('m', 'Male'), ('f', 'Female'), ('o', 'Others')], max_length=1),
        ),
    ]
