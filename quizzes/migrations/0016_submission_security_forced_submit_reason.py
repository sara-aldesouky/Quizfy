from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quizzes", "0015_quizsecurityviolation"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="security_forced_submit_reason",
            field=models.TextField(
                blank=True,
                help_text="Reason stored when the quiz was auto-submitted due to security violations",
                null=True,
            ),
        ),
    ]
