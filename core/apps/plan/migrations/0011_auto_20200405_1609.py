# Generated by Django 3.0 on 2020-04-05 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0010_auto_20200404_0541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userplan',
            name='actual_acute_load',
            field=models.FloatField(blank=True, default=0.0, help_text='actual acute load of a user in plan', null=True),
        ),
        migrations.AlterField(
            model_name='userplan',
            name='actual_freshness',
            field=models.FloatField(blank=True, default=0.0, help_text='actual freshness of a user in a plan', null=True),
        ),
        migrations.AlterField(
            model_name='userplan',
            name='actual_load',
            field=models.FloatField(blank=True, default=0.0, help_text='actual load of a user in plan', null=True),
        ),
        migrations.AlterField(
            model_name='userplan',
            name='actual_pss',
            field=models.FloatField(blank=True, default=0.0, help_text='actual pss of a user in plan', null=True),
        ),
    ]