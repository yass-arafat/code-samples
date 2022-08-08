# Generated by Django 3.0 on 2020-05-08 09:36

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('user_auth', '0003_userauthmodel_personalise_data'),
    ]

    operations = [
        migrations.RunSQL(
            "update user_auth as ua set personalise_data_id = upd.id"
            " from user_personalise_data as upd"
            " where upd.user_auth_id = ua.id"
        )
    ]