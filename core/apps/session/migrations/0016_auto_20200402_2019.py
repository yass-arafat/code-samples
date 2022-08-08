# Generated by Django 3.0 on 2020-04-02 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0015_auto_20200402_2008'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessiontype',
            name='type_name',
        ),
        migrations.AddField(
            model_name='sessiontype',
            name='code',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='sessiontype',
            name='name',
            field=models.CharField(max_length=55, null=True),
        ),
    ]
