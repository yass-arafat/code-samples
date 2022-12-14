# Generated by Django 3.0 on 2020-03-28 15:42

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0013_auto_20200327_1810'),
        ('plan', '0005_auto_20200326_2255'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='plan',
            name='date_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='user_event',
            field=models.ForeignKey(blank=True, help_text='event of this block', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plans', to='event.UserEvent'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='end_date',
            field=models.DateField(blank=True, help_text='end date of the plan'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='start_date',
            field=models.DateField(blank=True, help_text='start date of the plan'),
        ),
    ]
