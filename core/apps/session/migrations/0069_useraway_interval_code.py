# Generated by Django 3.0 on 2020-12-16 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0068_remove_useraway_away_interval'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraway',
            name='interval_code',
            field=models.UUIDField(blank=True, editable=False, help_text='away interval code', null=True),
        ),
    ]
