# Generated by Django 3.0 on 2020-10-26 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('week', '0025_auto_20200818_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='userweek',
            name='block_code',
            field=models.UUIDField(editable=False, help_text='Unique block', null=True),
        ),
    ]
