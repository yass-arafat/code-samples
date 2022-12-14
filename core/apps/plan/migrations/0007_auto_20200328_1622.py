# Generated by Django 3.0 on 2020-03-28 16:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0001_initial'),
        ('plan', '0006_auto_20200328_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='end_date',
            field=models.DateField(blank=True, help_text='end date of the plan', null=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='start_date',
            field=models.DateField(blank=True, help_text='start date of the plan', null=True),
        ),
        migrations.AlterField(
            model_name='plan',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserAuthModel'),
        ),
    ]
