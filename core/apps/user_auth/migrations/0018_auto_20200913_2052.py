# Generated by Django 3.0 on 2020-09-13 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0017_otp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='access_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='otp',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='verifier_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
