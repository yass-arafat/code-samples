# Generated by Django 3.0 on 2020-12-04 12:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0021_auto_20201019_1708'),
        ('session', '0061_auto_20200827_0123'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAway',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('away_date', models.DateField(blank=True, null=True)),
                ('reason', models.CharField(blank=True, max_length=200, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_auth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_away_days', to='user_auth.UserAuthModel')),
            ],
            options={
                'verbose_name': 'User Away',
                'db_table': 'user_away',
            },
        ),
    ]
