from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quizzes", "0013_studentfeedback"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentfeedback",
            name="practice_attempted_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When the student last submitted the saved practice question set",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="studentfeedback",
            name="practice_question_attempts",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Student's saved answers and results for generated practice questions",
            ),
        ),
    ]
