from django.db import models
from django.contrib.auth.models import User
import secrets
from django.core.validators import RegexValidator
from django.utils import timezone


numeric_only=RegexValidator(
    regex=r'^\d+$',
    message='University ID must contain digits only'
)

def question_image_upload_path(instance, filename):
    return f'quiz_images/quiz_{instance.quiz.id}/{filename}'
    
class Quiz(models.Model):
    title = models.CharField(max_length=60)
    code = models.CharField(max_length=40, unique=True, blank=True, null=True)
    folder = models.ForeignKey(
    "SubjectFolder",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="quizzes"
)
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quizzes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ Optional: quiz closes after this date/time
    due_at = models.DateTimeField(null=True, blank=True)

    # ✅ Timer in MINUTES (not seconds)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    # ✅ Teacher can stop/re-open quiz
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        """True if due_at exists and current time is past it."""
        return self.due_at is not None and timezone.now() > self.due_at

    def can_start(self):
        """Students can start only if teacher didn't stop it AND it's not expired."""
        return self.is_active and not self.is_expired()

    def save(self, *args, **kwargs):
        """Auto-generate a code if missing."""
        if not self.code:
            self.code = secrets.token_hex(3).upper()
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"{self.title} - {self.code}"
class Question(models.Model):
    quiz=models.ForeignKey(Quiz,on_delete=models.CASCADE,related_name='questions')
    text=models.TextField(blank=True)
    image=models.ImageField(upload_to=question_image_upload_path, blank=True , null=True)
    option1=models.CharField(max_length=60)
    option2=models.CharField(max_length=60)
    option3=models.CharField(max_length=60)
    option4=models.CharField(max_length=60)
    correct_option=models.IntegerField(choices=[
        (1,'Option 1'),(2,'Option 2'),(3,'Option 3'),(4,'Option 4')
    ])
    def option_text(self,number):
        return {
            1:self.option1,
            2:self.option2,
            3:self.option3,
            4:self.option4,
        }.get(number,"(blank)")               

    def __str__(self):
        return self.text[:60] if self.text else f"Question {self.id}"

class Submission(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="submissions")

    student_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions"
    )

    student_name = models.CharField(max_length=60)

    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    # ✅ timer tracking
    started_at = models.DateTimeField(null=True, blank=True)

    # ✅ attempt tracking

    attempt_no = models.PositiveIntegerField(default=1)

    # ✅ status
    is_submitted = models.BooleanField(default=False)

    # ✅ set when finalized (timer ends or student submits)
    submitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student_name} - {self.quiz.code} ({self.score}/{self.total})"

class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

class StudentProfile(models.Model):
    CITY_CHOICES = [
        ("Riyadh", "Riyadh"),
        ("Jeddah", "Jeddah"),
        ("Dammam", "Dammam"),
        ("Al-Ahsa", "Al-Ahsa"),
    ]

    MAJOR_CHOICES = [
        ("CS", "Computer Science"),
        ("IT", "Information Technology"),
        ("BUS", "Business"),
        ("LS", "Language Studies"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")

    first_name = models.CharField(max_length=60)
    second_name = models.CharField(max_length=60)
    third_name = models.CharField(max_length=60)

    university_id = models.CharField(max_length=30, unique=True)

    city = models.CharField(max_length=30, choices=CITY_CHOICES)
    major = models.CharField(max_length=30, choices=MAJOR_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.second_name} {self.third_name}".strip()


class SubjectFolder(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("teacher", "name")

    def __str__(self):
        return f"{self.name} ({self.teacher.username})"
class QuizAttemptPermission(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempt_permissions")
    student_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_permissions")
    allowed_attempts = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("quiz", "student_user")
    


# Create your models here.
