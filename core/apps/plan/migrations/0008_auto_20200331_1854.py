# Generated by Django 3.0 on 2020-03-31 18:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('block', '0017_auto_20200331_1849'),
        ('event', '0014_auto_20200331_1849'),
        ('user_auth', '0001_initial'),
        ('plan', '0007_auto_20200328_1622'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Plan',
            new_name='UserPlan',
        ),
        migrations.AlterModelOptions(
            name='userplan',
            options={'verbose_name': 'User Plan Table'},
        ),
    ]
