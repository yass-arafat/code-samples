# Generated by Django 3.0 on 2021-05-08 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0012_userplan_plan_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userplan',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='userplan',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Active'),
        ),
        migrations.AlterField(
            model_name='userplan',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
