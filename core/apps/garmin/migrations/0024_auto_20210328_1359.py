# Generated by Django 3.0 on 2021-03-28 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garmin', '0023_curvecalculationdata_activity_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='curvecalculationdata',
            name='athlete_activity_code',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='curvecalculationdata',
            name='ride_data_id',
            field=models.IntegerField(help_text='Stores related GarminData / StravaData ID based on source', null=True),
        ),
    ]
