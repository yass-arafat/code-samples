# Generated by Django 3.0 on 2020-10-19 14:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0051_auto_20201019_1324'),
    ]

    operations = [
        migrations.RunSQL(
            "update user_profile as upd set user_auth_id = ua.id"
            " from user_auth as ua"
            " where upd.id = ua.profile_data_id"
        ),
        migrations.RunSQL(
            "update user_personalise_data as usd set user_auth_id = ua.id"
            " from user_auth as ua"
            " where usd.id = ua.personalise_data_id"
        )
    ]
