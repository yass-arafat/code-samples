# Generated by Django 3.0 on 2021-06-28 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('block', '0025_auto_20201025_0651'),
    ]

    operations = [
        migrations.AddField(
            model_name='userblock',
            name='user_id',
            field=models.UUIDField(null=True),
        ),
    ]
