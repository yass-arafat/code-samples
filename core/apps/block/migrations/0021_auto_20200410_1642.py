# Generated by Django 3.0 on 2020-04-10 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('block', '0020_auto_20200410_1337'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userblock',
            name='number',
            field=models.IntegerField(default=1, help_text='block number'),
            preserve_default=False,
        ),
    ]
