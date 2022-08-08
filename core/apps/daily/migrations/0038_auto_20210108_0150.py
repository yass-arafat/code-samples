# Generated by Django 3.0 on 2021-01-08 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily', '0037_auto_20201126_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualday',
            name='prs_accuracy_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='PRS Score calculated using SAS_today', max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='actualday',
            name='sas_today',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='actualday',
            name='prs_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='PRS Score calculated using SQS_today', max_digits=20, null=True),
        ),
    ]