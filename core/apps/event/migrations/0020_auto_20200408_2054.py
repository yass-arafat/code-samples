# Generated by Django 3.0 on 2020-04-08 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0019_auto_20200404_0541'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventdemandstruthtable',
            options={'verbose_name': 'Event Demands Table'},
        ),
        migrations.AlterModelTable(
            name='eventdemandstruthtable',
            table='event_demands',
        ),
    ]