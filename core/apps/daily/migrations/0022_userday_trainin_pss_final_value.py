# Generated by Django 3.0 on 2020-04-08 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0021_userday_commute_pss_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='userday',
            name='trainin_pss_final_value',
            field=models.FloatField(blank=True, help_text='minimum of four different pss', null=True),
        ),
    ]
