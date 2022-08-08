# Generated by Django 3.0 on 2020-04-18 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0028_auto_20200418_1832'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z0',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z1',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z2',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z3',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z4',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z5',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z6',
        ),
        migrations.RemoveField(
            model_name='userday',
            name='time_in_Z7',
        ),
        migrations.AddField(
            model_name='userday',
            name='actual_time_in_zones',
            field=models.TextField(blank=True, help_text='User actual time in zone 0-7', null=True),
        ),
        migrations.AddField(
            model_name='userday',
            name='planned_time_in_zones',
            field=models.TextField(blank=True, help_text='User planned time in zone 0-7', null=True),
        ),
        migrations.AlterField(
            model_name='userday',
            name='actual_freshness',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='actual freshness of a user in a day', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='acute_load_post_commute',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Acute Load post commute for day n', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='commute_pss_day',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='commute pss of a user in day', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='load_post_commute',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Load post commute for day n', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='max_acute_load',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='max_freshness',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='max_load',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='max_pss',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='planned_freshness',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='planned_pss',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='actual load of a user in day', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='training_pss_by_freshness',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Training PSS freshness approach', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='training_pss_by_hours',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Training PSS max hours approach', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='training_pss_by_load',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Training PSS load approach', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='training_pss_by_max_ride',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Training PSS max load approach', max_digits=20),
        ),
        migrations.AlterField(
            model_name='userday',
            name='training_pss_final_value',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='minimum of four different pss', max_digits=20),
        ),
    ]