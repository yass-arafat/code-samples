# Generated by Django 3.0 on 2020-10-20 05:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0012_merge_20201020_0531'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usernotificationsetting',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='usernotificationsetting',
            name='updated_at',
        ),
    ]
