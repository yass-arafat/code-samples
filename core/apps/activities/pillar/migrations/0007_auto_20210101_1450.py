# Generated by Django 3.0 on 2021-01-01 14:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pillar', '0006_migrate_pillar_data_fields_to_actual_session'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='activity_description',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='label',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='name',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='stress_level',
        ),
    ]
