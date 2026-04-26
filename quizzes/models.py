"""
=============================================================================
Quizfy Models
=============================================================================

This module defines all database models for the Quizfy quiz platform.

Models Overview:
----------------
- Quiz              : Represents a quiz with settings (timer, due date, etc.)
- Question          : A question within a quiz (multiple choice, true/false, file upload)
- Submission        : A student's quiz attempt and results
- Answer            : Individual answer to a question within a submission
- StudentProfile    : Extended profile information for student users
- SubjectFolder     : Organizes quizzes into subject/course folders
- QuizAttemptPermission : Controls how many attempts a student can make
- FileSubmission    : Stores uploaded files for file-upload type questions

Author: Quizfy Team
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone

import secrets
import qrcode
from io import BytesIO
import base64


# =============================================================================
# VALIDATORS
# =============================================================================

# Validator for university ID - must contain only digits
numeric_only = RegexValidator(
    regex=r'^\d+$',
    message='University ID must contain digits only'
)


# =============================================================================
# FILE UPLOAD PATH FUNCTIONS
# =============================================================================

def question_image_upload_path(instance, filename):
    """
    Generate upload path for question images.
    Path: quiz_images/quiz_{quiz_id}/{filename}
    """
    return f'quiz_images/quiz_{instance.quiz.id}/{filename}'


def file_submission_upload_path(instance, filename):
    """
    Generate upload path for student file submissions.
    Path: file_submissions/quiz_{quiz_id}/{student_id}/{filename}
    """
    student_id = instance.submission.student_user.id if instance.submission.student_user else "anon"
    return f'file_submissions/quiz_{instance.submission.quiz.id}/{student_id}/{filename}'


def teacher_feedback_file_path(instance, filename):
    """
    Generate upload path for teacher feedback files on submissions.
    Path: teacher_feedback/submission_{submission_id}/{filename}
    """
    return f"teacher_feedback/submission_{instance.id}/{filename}"


def teacher_feedback_upload_path(instance, filename):
    """
    Generate upload path for teacher feedback files on FileSubmission objects.
    Path: teacher_feedback/quiz_{quiz_id}/{student_id}/{filename}
    """
    student_id = instance.submission.student_user.id if instance.submission.student_user else "anon"
    return f'teacher_feedback/quiz_{instance.submission.quiz.id}/{student_id}/{filename}'


# =============================================================================
# QUIZ MODEL
# =============================================================================

class Quiz(models.Model):
    """
    Represents a quiz created by a teacher.
    
    Features:
    - Multiple quiz types (multiple choice, true/false, file upload)
    - Optional timer (duration in minutes)
    - Optional due date
    - Can be organized into folders
    - Unique access code for students
    - QR code generation for easy access
    """
    
    # Quiz type choices
    QUIZ_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True / False'),
        ('file_upload', 'File Upload (PDF/Photo)'),
    ]
    
    # Basic information
    title = models.CharField(
        max_length=60,
        help_text="Quiz title displayed to students"
    )
    code = models.CharField(
        max_length=40, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Unique code for students to access the quiz"
    )
    quiz_type = models.CharField(
        max_length=20, 
        choices=QUIZ_TYPE_CHOICES, 
        default='multiple_choice',
        help_text="Type of questions in this quiz"
    )
    
    # Relationships
    folder = models.ForeignKey(
        "SubjectFolder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quizzes",
        help_text="Optional folder to organize this quiz"
    )
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="quizzes",
        help_text="The teacher who created this quiz"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Quiz settings
    due_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Quiz closes after this date/time (optional)"
    )
    duration_minutes = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Time limit in minutes (optional)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Teacher can stop/re-open quiz"
    )

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        ordering = ['-created_at']

    def is_expired(self):
        """Check if the quiz has passed its due date."""
        return self.due_at is not None and timezone.now() > self.due_at

    def can_start(self):
        """
        Check if students can start this quiz.
        Returns True only if:
        - Teacher hasn't stopped the quiz (is_active=True)
        - Quiz hasn't expired (due_at not passed)
        """
        return self.is_active and not self.is_expired()

    def get_qr_code_base64(self):
        """
        Generate a QR code that points to the quiz URL.
        Returns base64-encoded PNG image or empty string on error.
        """
        try:
            qr_data = f"/quiz/{self.code}/"
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            print(f"QR Code generation error for {self.code}: {e}")
            return ""

    def save(self, *args, **kwargs):
        """Auto-generate a unique 6-character code if not provided."""
        if not self.code:
            self.code = secrets.token_hex(3).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.code}"


# =============================================================================
# QUESTION MODEL
# =============================================================================

class Question(models.Model):
    """
    Represents a single question within a quiz.
    
    Supports three types:
    - Multiple Choice: 4 options, one correct answer
    - True/False: 2 options (True/False), one correct
    - File Upload: Student uploads a file as their answer (graded manually)
    """
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice (4 options)'),
        ('true_false', 'True / False'),
        ('file_upload', 'File Upload (Student uploads file)'),
    ]
    
    # Relationship to quiz
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    
    # Question content
    question_type = models.CharField(
        max_length=20, 
        choices=QUESTION_TYPE_CHOICES, 
        default='multiple_choice'
    )
    text = models.TextField(
        blank=True,
        help_text="The question text"
    )
    image = models.ImageField(
        upload_to=question_image_upload_path, 
        blank=True, 
        null=True,
        help_text="Optional image for the question"
    )
    
    # Answer options (used for multiple choice and true/false)
    option1 = models.CharField(max_length=60, blank=True, default='')
    option2 = models.CharField(max_length=60, blank=True, default='')
    option3 = models.CharField(max_length=60, blank=True, default='')
    option4 = models.CharField(max_length=60, blank=True, default='')
    
    # Correct answer (1-4 for multiple choice, 1=True/2=False for true/false)
    correct_option = models.IntegerField(
        choices=[
            (1, 'Option 1 / True'),
            (2, 'Option 2 / False'),
            (3, 'Option 3'),
            (4, 'Option 4')
        ], 
        default=1
    )

    class Meta:
        ordering = ['id']

    def option_text(self, number):
        """Get the text for a specific option number (1-4)."""
        return {
            1: self.option1,
            2: self.option2,
            3: self.option3,
            4: self.option4,
        }.get(number, "(blank)")

    def __str__(self):
        return self.text[:60] if self.text else f"Question {self.id}"


# =============================================================================
# SUBMISSION MODEL
# =============================================================================

class Submission(models.Model):
    """
    Represents a student's attempt at a quiz.
    
    Tracks:
    - Score and total questions
    - Start and submit times (for timer)
    - Attempt number (for multiple attempts)
    - Teacher grading (for file upload quizzes)
    """
    
    # Relationships
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name="submissions"
    )
    student_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="submissions",
        help_text="The student who made this submission"
    )
    
    # Student identification (backup if user is deleted)
    student_name = models.CharField(max_length=60)
    
    # Scoring
    score = models.IntegerField(default=0, help_text="Number of correct answers")
    total = models.IntegerField(default=0, help_text="Total number of questions")
    
    # Timer tracking
    started_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the student started the quiz"
    )
    submitted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the quiz was submitted (timer end or manual submit)"
    )
    
    # Attempt tracking
    attempt_no = models.PositiveIntegerField(
        default=1,
        help_text="Which attempt this is for the student"
    )
    is_submitted = models.BooleanField(
        default=False,
        help_text="Whether this submission has been finalized"
    )
    
    # Teacher grading fields (for file upload quizzes)
    teacher_comment = models.TextField(
        blank=True, 
        null=True,
        help_text="Teacher's feedback comment"
    )
    manual_grade = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Manual grade (e.g., 'A', 'B+', '85%', 'Pass')"
    )
    teacher_file = models.FileField(
        upload_to=teacher_feedback_file_path, 
        blank=True, 
        null=True,
        help_text="Teacher's corrected/feedback file"
    )
    teacher_file_name = models.CharField(max_length=255, blank=True, null=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at', '-id']

    def __str__(self):
        return f"{self.student_name} - {self.quiz.code} ({self.score}/{self.total})"


# =============================================================================
# ANSWER MODEL
# =============================================================================

class Answer(models.Model):
    """
    Represents a student's answer to a single question.
    Links a Submission to a Question with the selected option.
    """
    
    submission = models.ForeignKey(
        Submission, 
        on_delete=models.CASCADE, 
        related_name='answers'
    )
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE
    )
    selected = models.IntegerField(
        null=True, 
        blank=True,
        help_text="The option number selected (1-4)"
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['question__id']


# =============================================================================
# STUDENT PROFILE MODEL
# =============================================================================

class StudentProfile(models.Model):
    """
    Extended profile information for student users.
    Stores additional data not in the default Django User model.
    """
    
    # City choices (Saudi Arabia)
    CITY_CHOICES = [
        ("Riyadh", "Riyadh"),
        ("Jeddah", "Jeddah"),
        ("Dammam", "Dammam"),
        ("Al-Ahsa", "Al-Ahsa"),
        ("Hail", "Hail"),
        ("Madinah", "Madinah"),
    ]

    # Major/field of study choices
    MAJOR_CHOICES = [
        ("CS", "Computer Science"),
        ("IT", "Information Technology"),
        ("BUS", "Business"),
        ("LS", "Language Studies"),
    ]

    # Link to Django User model (one-to-one relationship)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="student_profile"
    )

    # Student's full name (split into three parts as per Arabic naming convention)
    first_name = models.CharField(max_length=60)
    second_name = models.CharField(max_length=60)
    third_name = models.CharField(max_length=60)

    # University ID (unique identifier)
    university_id = models.CharField(
        max_length=30, 
        unique=True,
        help_text="Student's university ID number"
    )

    # Location and study information
    city = models.CharField(max_length=30, choices=CITY_CHOICES)
    major = models.CharField(max_length=30, choices=MAJOR_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.second_name} {self.third_name}".strip()


# =============================================================================
# SUBJECT FOLDER MODEL
# =============================================================================

class SubjectFolder(models.Model):
    """
    Organizes quizzes into subject/course folders for a teacher.
    
    Each teacher can have multiple folders, and each folder name
    must be unique per teacher.
    """
    
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="folders"
    )
    name = models.CharField(
        max_length=80,
        help_text="Folder name (e.g., 'Physics 101', 'Math Fall 2024')"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("teacher", "name")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.teacher.username})"


# =============================================================================
# QUIZ ATTEMPT PERMISSION MODEL
# =============================================================================

class QuizAttemptPermission(models.Model):
    """
    Controls how many attempts a student can make on a specific quiz.
    
    By default, students get 1 attempt. Teachers can grant extra attempts
    for individual students (e.g., for technical issues or retakes).
    """
    
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name="attempt_permissions"
    )
    student_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="quiz_permissions"
    )
    allowed_attempts = models.PositiveIntegerField(
        default=1,
        help_text="Number of attempts allowed for this student"
    )

    class Meta:
        unique_together = ("quiz", "student_user")


# =============================================================================
# FILE SUBMISSION MODEL
# =============================================================================

class FileSubmission(models.Model):
    """
    Stores uploaded files for file_upload type quizzes or questions.
    
    Supports:
    - Quiz-level file uploads (entire quiz is one file upload)
    - Question-level file uploads (specific questions require file uploads)
    - Teacher grading with comments and feedback files
    """
    
    # Relationships
    submission = models.ForeignKey(
        Submission, 
        on_delete=models.CASCADE, 
        related_name="file_submissions"
    )
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="file_answers",
        help_text="Link to specific question (null for quiz-level uploads)"
    )
    
    # Student's uploaded file
    file = models.FileField(upload_to=file_submission_upload_path)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Teacher grading fields
    teacher_comment = models.TextField(
        blank=True, 
        null=True,
        help_text="Teacher's feedback comment"
    )
    grade = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Grade (e.g., 'A', 'B', '85%')"
    )
    teacher_file = models.FileField(
        upload_to=teacher_feedback_upload_path, 
        blank=True, 
        null=True,
        help_text="Teacher's corrected/feedback file"
    )
    teacher_file_name = models.CharField(max_length=255, blank=True, null=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.file_name} - {self.submission.student_name}"


# =============================================================================
# STUDENT FEEDBACK MODEL
# =============================================================================

class StudentFeedback(models.Model):
    """
    Stores AI-generated personalized learning feedback for a student's quiz submission.
    
    Generated immediately after quiz submission, includes:
    - Weak topics identified from incorrect answers
    - Mistake patterns (conceptual, careless, repeated)
    - Flashcards for revision
    - Practice questions at adaptive difficulty
    - Step-by-step solutions
    """
    
    # Relationships
    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text="The quiz submission this feedback is for"
    )
    
    # Feedback data (stored as JSON)
    weak_topics = models.JSONField(
        default=list,
        blank=True,
        help_text="List of identified weak topics with explanations"
    )
    flashcards = models.JSONField(
        default=list,
        blank=True,
        help_text="Flashcards for revision on weak topics"
    )
    practice_questions = models.JSONField(
        default=list,
        blank=True,
        help_text="Generated practice questions with solutions"
    )
    practice_question_attempts = models.JSONField(
        default=list,
        blank=True,
        help_text="Student's saved answers and results for generated practice questions"
    )

    # Metadata
    generated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the feedback was generated"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update time"
    )
    generation_error = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if feedback generation failed"
    )
    
    # Tracking
    viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student first viewed this feedback"
    )
    practice_attempted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student last submitted the saved practice question set"
    )
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Feedback for {self.submission.student_name} - {self.submission.quiz.code}"
    
    def mark_as_viewed(self):
        """Mark feedback as viewed by student."""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])


# =============================================================================
# QUIZ SECURITY VIOLATION MODEL
# =============================================================================

class QuizSecurityViolation(models.Model):
    """Stores suspicious actions detected while a student is taking a quiz."""

    TAB_SWITCH = "TAB_SWITCH"
    FULLSCREEN_EXIT = "FULLSCREEN_EXIT"
    WINDOW_BLUR = "WINDOW_BLUR"
    COPY_ATTEMPT = "COPY_ATTEMPT"
    RIGHT_CLICK = "RIGHT_CLICK"
    DEVTOOLS_SHORTCUT = "DEVTOOLS_SHORTCUT"
    PRINT_ATTEMPT = "PRINT_ATTEMPT"

    VIOLATION_TYPE_CHOICES = [
        (TAB_SWITCH, "Tab Switch"),
        (FULLSCREEN_EXIT, "Fullscreen Exit"),
        (WINDOW_BLUR, "Window Blur"),
        (COPY_ATTEMPT, "Copy Attempt"),
        (RIGHT_CLICK, "Right Click"),
        (DEVTOOLS_SHORTCUT, "Developer Tools Shortcut"),
        (PRINT_ATTEMPT, "Print Attempt"),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quiz_security_violations",
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="security_violations",
    )
    attempt = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="security_violations",
    )
    violation_type = models.CharField(
        max_length=32,
        choices=VIOLATION_TYPE_CHOICES,
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the security violation was recorded",
    )
    details = models.TextField(
        blank=True,
        null=True,
        help_text="Optional extra details captured by the frontend detector",
    )

    class Meta:
        ordering = ["-timestamp", "-id"]

    def __str__(self):
        return f"{self.student.username} - {self.quiz.code} - {self.violation_type}"
