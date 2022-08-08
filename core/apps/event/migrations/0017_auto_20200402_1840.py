# Generated by Django 3.0 on 2020-04-02 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0016_auto_20200402_2322'),
    ]

    operations = [
        migrations.RenameField(
            model_name='namedevent',
            old_name='event_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='userevent',
            old_name='event_date',
            new_name='date',
        ),
        migrations.RenameField(
            model_name='userevent',
            old_name='event_name',
            new_name='name',
        ),
        migrations.AddField(
            model_name='userevent',
            name='created_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userevent',
            name='is_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userevent',
            name='updated_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='eventtype',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='namedevent',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='userevent',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]