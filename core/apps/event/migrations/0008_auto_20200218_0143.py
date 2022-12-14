# Generated by Django 3.0 on 2020-02-17 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0007_auto_20200212_2344'),
    ]

    operations = [
        migrations.AddField(
            model_name='userevent',
            name='user_created_event_sub_type',
            field=models.IntegerField(blank=True, choices=[(1, 'Flat'), (2, 'Hilly'), (3, 'Mountain'), (4, 'Ten Miles'), (5, '25 miles'), (6, '50+ plus'), (7, 'Short'), (8, 'Long'), (9, 'Flat or Rolling'), (10, 'Olympic'), (11, 'Half Ironman'), (12, 'Ironman')], null=True),
        ),
        migrations.AddField(
            model_name='userevent',
            name='user_created_event_type',
            field=models.IntegerField(blank=True, choices=[(1, 'Sportive'), (2, 'Multi-Day'), (3, 'Time Trial'), (4, 'Criterium'), (5, 'Road Race'), (6, 'Zwift Race'), (7, 'Triathlon'), (8, 'Fitness')], null=True),
        ),
        migrations.AlterField(
            model_name='eventtype',
            name='sub_type',
            field=models.IntegerField(choices=[(1, 'Flat'), (2, 'Hilly'), (3, 'Mountain'), (4, 'Ten Miles'), (5, '25 miles'), (6, '50+ plus'), (7, 'Short'), (8, 'Long'), (9, 'Flat or Rolling'), (10, 'Olympic'), (11, 'Half Ironman'), (12, 'Ironman')], null=True),
        ),
        migrations.AlterField(
            model_name='userevent',
            name='performance_goal',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
