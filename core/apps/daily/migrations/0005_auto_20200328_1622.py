# Generated by Django 3.0 on 2020-03-28 16:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0001_initial'),
        ('daily', '0004_auto_20200328_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='daily',
            name='user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserAuthModel'),
        ),
    ]