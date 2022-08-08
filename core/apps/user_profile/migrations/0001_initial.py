# Generated by Django 3.0 on 2020-01-12 15:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('sex', models.CharField(blank=True, max_length=10, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=50, null=True)),
                ('user_auth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserAuthModel')),
            ],
            options={
                'verbose_name': 'User Profile Table',
                'db_table': 'user_profile',
            },
        ),
    ]
