# Generated by Django 3.0 on 2021-01-08 00:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0072_auto_20201230_2025'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='key_zones',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='sessionscore',
            name='duration_accuracy_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Duration Score calculated using SAS algorithm', max_digits=20),
        ),
        migrations.AddField(
            model_name='sessionscore',
            name='intensity_accuracy_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Intensity Score calculated using SAS algorithm', max_digits=20),
        ),
        migrations.AddField(
            model_name='sessionscore',
            name='key_zone_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Key Zone Score calculated using SAS algorithm', max_digits=20),
        ),
        migrations.AddField(
            model_name='sessionscore',
            name='non_key_zone_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Non Key Zone Score calculated using SAS algorithm', max_digits=20),
        ),
        migrations.AddField(
            model_name='sessionscore',
            name='overall_accuracy_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Overall Score calculated using SAS algorithm', max_digits=20),
        ),
        migrations.AddField(
            model_name='sessionscore',
            name='prs_accuracy_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='PRS Score calculated using SAS algorithm', max_digits=20),
        ),
        migrations.AddField(
            model_name='sessionscore',
            name='sas_today_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='SAS Today Score calculated using SAS algorithm', max_digits=20),
        ),
        migrations.AlterField(
            model_name='sessionscore',
            name='duration_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Duration Score calculated using SQS algorithm', max_digits=20),
        ),
        migrations.AlterField(
            model_name='sessionscore',
            name='overall_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Overall Score calculated using SQS algorithm', max_digits=20),
        ),
        migrations.AlterField(
            model_name='sessionscore',
            name='prs_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='PRS Score calculated using SQS algorithm', max_digits=20),
        ),
        migrations.AlterField(
            model_name='sessionscore',
            name='sqs_session_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Intensity Score calculated using SQS algorithm', max_digits=20),
        ),
        migrations.AlterField(
            model_name='sessionscore',
            name='sqs_today_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='SQS Today Score calculated using SQS algorithm', max_digits=20),
        ),
    ]
