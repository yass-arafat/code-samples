# Generated by Django 3.0 on 2020-03-31 18:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('block', '0015_auto_20200331_1814'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userblock',
            options={'verbose_name': 'Block Table'},
        ),
        migrations.AlterModelTable(
            name='userblock',
            table='user_block_plan',
        ),
    ]
