# Generated by Django 3.0 on 2020-03-27 14:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0011_namedevent_climbing_ratio'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventDemandsTruthTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zone1_priority', models.IntegerField(blank=True, default=0, null=True)),
                ('zone2_priority', models.IntegerField(blank=True, default=0, null=True)),
                ('zone3_priority', models.IntegerField(blank=True, default=0, null=True)),
                ('zone4_priority', models.IntegerField(blank=True, default=0, null=True)),
                ('zone5_priority', models.IntegerField(blank=True, default=0, null=True)),
                ('zone6_priority', models.IntegerField(blank=True, default=0, null=True)),
                ('zone7_priority', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='eventtype',
            name='ed_truth_table',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='event_types', to='event.EventDemandsTruthTable'),
        ),
    ]
