# Generated by Django 3.0 on 2021-06-28 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pillar', '0009_auto_20210302_0642'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
    ]