# Generated by Django 3.0 on 2020-06-27 18:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0022_auto_20200627_1653'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserActivityCode',
            new_name='UserActivityType',
        ),
        migrations.AlterModelOptions(
            name='useractivitytype',
            options={'verbose_name': 'User Activity Type TT'},
        ),
        migrations.AlterModelTable(
            name='useractivitytype',
            table='user_activity_type',
        ),
    ]
