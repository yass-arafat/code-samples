from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0072_auto_20201230_2025'),
        ('pillar', '0005_auto_20201210_1002'),
        ('user_profile', '0069_auto_20201230_2206')
    ]

    operations = [
        migrations.RunSQL(
            "update actual_session as actual set activity_name = pd.name"
            " from pillar_data as pd"
            " where actual.pillar_data_id = pd.id"
        ),
        migrations.RunSQL(
            "update actual_session as actual set session_label = pd.label"
            " from pillar_data as pd"
            " where actual.pillar_data_id = pd.id"
        ),
        migrations.RunSQL(
            "update actual_session as actual set description = pd.activity_description"
            " from pillar_data as pd"
            " where actual.pillar_data_id = pd.id"
        ),
        migrations.RunSQL(
            "update actual_session as actual set effort_level = pd.stress_level"
            " from pillar_data as pd"
            " where actual.pillar_data_id = pd.id"
        )
    ]
