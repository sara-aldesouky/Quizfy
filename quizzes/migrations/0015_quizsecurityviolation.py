from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("quizzes", "0014_studentfeedback_practice_attempts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="QuizSecurityViolation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("violation_type", models.CharField(choices=[("TAB_SWITCH", "Tab Switch"), ("FULLSCREEN_EXIT", "Fullscreen Exit"), ("WINDOW_BLUR", "Window Blur"), ("COPY_ATTEMPT", "Copy Attempt"), ("RIGHT_CLICK", "Right Click"), ("DEVTOOLS_SHORTCUT", "Developer Tools Shortcut"), ("PRINT_ATTEMPT", "Print Attempt")], max_length=32)),
                ("timestamp", models.DateTimeField(auto_now_add=True, help_text="When the security violation was recorded")),
                ("details", models.TextField(blank=True, help_text="Optional extra details captured by the frontend detector", null=True)),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="security_violations", to="quizzes.submission")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="security_violations", to="quizzes.quiz")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_security_violations", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-timestamp", "-id"],
            },
        ),
    ]
