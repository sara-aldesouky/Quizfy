"""
=============================================================================
Quizfy Admin Configuration
=============================================================================

This module configures the Django admin interface for the Quizfy application.

Admin Classes:
--------------
- QuizAdmin           : Manage quizzes with list display, filters, and search
- QuestionAdmin       : Manage questions with quiz filtering
- SubmissionAdmin     : View and manage student submissions
- AnswerAdmin         : View individual answers (read-only)
- StudentProfileAdmin : Manage student profiles
- SubjectFolderAdmin  : Manage subject folders
- FileSubmissionAdmin : View file uploads and teacher grading

Author: Quizfy Team
=============================================================================
"""

from django.contrib import admin
from .models import (
    Quiz, Question, Submission, Answer, 
    StudentProfile, SubjectFolder, QuizAttemptPermission, FileSubmission,
    QuizSecurityViolation,
)


# =============================================================================
# QUIZ ADMIN
# =============================================================================

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin interface for Quiz model."""
    
    list_display = ('title', 'code', 'quiz_type', 'teacher', 'is_active', 'created_at')
    list_filter = ('quiz_type', 'is_active', 'created_at', 'folder')
    search_fields = ('title', 'code', 'teacher__username')
    readonly_fields = ('code', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'code', 'quiz_type', 'teacher', 'folder')
        }),
        ('Settings', {
            'fields': ('is_active', 'duration_minutes', 'due_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# =============================================================================
# QUESTION ADMIN
# =============================================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model."""
    
    list_display = ('id', 'quiz', 'question_type', 'text_preview', 'correct_option')
    list_filter = ('question_type', 'quiz')
    search_fields = ('text', 'quiz__title')
    raw_id_fields = ('quiz',)
    
    def text_preview(self, obj):
        """Show first 50 characters of question text."""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question Text'


# =============================================================================
# SUBMISSION ADMIN
# =============================================================================

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin interface for Submission model."""
    
    list_display = (
        'id', 'quiz', 'student_name', 'score', 'total', 
        'is_submitted', 'submitted_at'
    )
    list_filter = ('is_submitted', 'quiz', 'submitted_at')
    search_fields = ('student_name', 'student_user__username', 'quiz__title')
    readonly_fields = ('started_at', 'submitted_at', 'graded_at')
    raw_id_fields = ('quiz', 'student_user')
    ordering = ('-submitted_at',)
    
    fieldsets = (
        ('Student Information', {
            'fields': ('quiz', 'student_user', 'student_name')
        }),
        ('Score', {
            'fields': ('score', 'total', 'attempt_no')
        }),
        ('Status', {
            'fields': ('is_submitted', 'started_at', 'submitted_at')
        }),
        ('Teacher Grading', {
            'fields': ('manual_grade', 'teacher_comment', 'teacher_file', 'graded_at'),
            'classes': ('collapse',)
        }),
    )


# =============================================================================
# ANSWER ADMIN
# =============================================================================

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Admin interface for Answer model (read-only)."""
    
    list_display = ('id', 'submission', 'question', 'selected', 'is_correct')
    list_filter = ('is_correct',)
    raw_id_fields = ('submission', 'question')
    readonly_fields = ('submission', 'question', 'selected', 'is_correct')


# =============================================================================
# STUDENT PROFILE ADMIN
# =============================================================================

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for StudentProfile model."""
    
    list_display = ('full_name', 'university_id', 'user', 'city', 'major')
    list_filter = ('city', 'major')
    search_fields = ('first_name', 'second_name', 'third_name', 'university_id', 'user__username')
    raw_id_fields = ('user',)
    
    def full_name(self, obj):
        """Display student's full name."""
        return f"{obj.first_name} {obj.second_name} {obj.third_name}"
    full_name.short_description = 'Full Name'


# =============================================================================
# SUBJECT FOLDER ADMIN
# =============================================================================

@admin.register(SubjectFolder)
class SubjectFolderAdmin(admin.ModelAdmin):
    """Admin interface for SubjectFolder model."""
    
    list_display = ('name', 'teacher', 'quiz_count', 'created_at')
    list_filter = ('teacher', 'created_at')
    search_fields = ('name', 'teacher__username')
    ordering = ('name',)
    
    def quiz_count(self, obj):
        """Display number of quizzes in folder."""
        return obj.quizzes.count()
    quiz_count.short_description = 'Quizzes'


# =============================================================================
# QUIZ ATTEMPT PERMISSION ADMIN
# =============================================================================

@admin.register(QuizAttemptPermission)
class QuizAttemptPermissionAdmin(admin.ModelAdmin):
    """Admin interface for QuizAttemptPermission model."""
    
    list_display = ('quiz', 'student_user', 'allowed_attempts')
    list_filter = ('quiz',)
    search_fields = ('quiz__title', 'student_user__username')
    raw_id_fields = ('quiz', 'student_user')


# =============================================================================
# FILE SUBMISSION ADMIN
# =============================================================================

@admin.register(FileSubmission)
class FileSubmissionAdmin(admin.ModelAdmin):
    """Admin interface for FileSubmission model."""
    
    list_display = ('id', 'submission', 'file_name', 'grade', 'uploaded_at', 'graded_at')
    list_filter = ('uploaded_at', 'graded_at')
    search_fields = ('file_name', 'submission__student_name')
    raw_id_fields = ('submission', 'question')
    readonly_fields = ('uploaded_at',)
    
    fieldsets = (
        ('File Information', {
            'fields': ('submission', 'question', 'file', 'file_name', 'uploaded_at')
        }),
        ('Teacher Grading', {
            'fields': ('grade', 'teacher_comment', 'teacher_file', 'teacher_file_name', 'graded_at')
        }),
    )


@admin.register(QuizSecurityViolation)
class QuizSecurityViolationAdmin(admin.ModelAdmin):
    """Admin interface for quiz security violations."""

    list_display = ("id", "quiz", "student", "attempt", "violation_type", "timestamp")
    list_filter = ("violation_type", "quiz", "timestamp")
    search_fields = ("student__username", "quiz__title", "quiz__code", "details")
    raw_id_fields = ("student", "quiz", "attempt")
    readonly_fields = ("timestamp",)
