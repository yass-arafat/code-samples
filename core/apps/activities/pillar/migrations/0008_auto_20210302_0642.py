# Generated by Django 3.0 on 2021-03-02 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pillar', '0007_auto_20210101_1450'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='type',
            field=models.CharField(default='cycling', help_text='Type of the Activity', max_length=55),
            preserve_default=False,
        ),
    ]
