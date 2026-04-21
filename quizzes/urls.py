"""
=============================================================================
Quizfy Application URL Configuration
=============================================================================

This module defines all URL patterns for the Quizfy quiz application.

URL Categories:
---------------
1. Public Routes           - Landing page, home
2. Quiz Access Routes      - Taking quizzes, QR codes, results
3. Teacher Auth Routes     - Teacher login, signup, logout
4. Teacher Quiz Routes     - Create, edit, delete quizzes
5. Teacher Question Routes - Manage questions within quizzes
6. Teacher Submission Routes - View and grade submissions
7. Teacher Folder Routes   - Organize quizzes into folders
8. Teacher Export Routes   - Download Excel reports
9. Student Auth Routes     - Student login, signup
10. Student Dashboard Routes - View submissions, enter quizzes
11. Password Reset Routes  - Forgot password flow
12. Password Change Routes - Change password while logged in

Author: Quizfy Team
=============================================================================
"""

from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.http import HttpResponse

from . import views


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    
    # =========================================================================
    # PUBLIC ROUTES
    # =========================================================================
    
    # Home page - redirects based on user type (teacher/student)
    path("", views.home, name="home"),
    
    # Landing page - always shows marketing page (no redirect)
    path("landing/", views.landing, name="landing"),
    
    # Logout - works for both teachers and students
    path("logout/", views.app_logout, name="app_logout"),
    
    
    # =========================================================================
    # QUIZ ACCESS ROUTES (Students taking quizzes)
    # =========================================================================
    
    # Quiz result page - show score and answers after submission
    path(
        "quiz/<str:quiz_code>/result/<int:submission_id>/", 
        views.quiz_result, 
        name="quiz_result"
    ),
    
    # Generate QR code image for a quiz
    path("quiz/<str:quiz_code>/qr/", views.quiz_qr_code, name="quiz_qr_code"),
    
    # Quiz join page - shown when QR code is scanned
    path("quiz/<str:quiz_code>/join/", views.quiz_join, name="quiz_join"),
    
    # QR scan redirect - handles authentication flow for QR scans
    path("quiz/<str:quiz_code>/scan/", views.quiz_scan_redirect, name="quiz_scan_redirect"),
    
    # Check quiz status (AJAX endpoint)
    path("quiz/<str:quiz_code>/status/", views.quiz_status, name="quiz_status"),
    
    # Take quiz - main quiz-taking interface (must be last quiz pattern)
    path("quiz/<str:quiz_code>/", views.take_quiz, name="take_quiz"),
    
    
    # =========================================================================
    # TEACHER AUTHENTICATION ROUTES
    # =========================================================================
    
    path("teacher/signup/", views.teacher_signup, name="teacher_signup"),
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    
    
    # =========================================================================
    # TEACHER QUIZ MANAGEMENT ROUTES
    # =========================================================================
    
    # Dashboard - list all quizzes and folders
    path("teacher/quizzes/", views.teacher_quizzes, name="teacher_quizzes"),
    
    # Create new quiz
    path("teacher/quizzes/create/", views.create_quiz, name="create_quiz"),
    
    # Get live submission counts (AJAX endpoint)
    path("teacher/quizzes/live-counts/", views.quiz_live_counts, name="quiz_live_counts"),

    # Full-class PDF + Excel RAG analytics test page
    path(
        "teacher/performance-analytics/",
        views.performance_analytics_dashboard,
        name="performance_analytics_dashboard",
    ),
    
    # Quiz detail view
    path(
        "teacher/quizzes/<int:quiz_id>/", 
        views.teacher_quiz_detail, 
        name="teacher_quiz_detail"
    ),
    
    # Delete quiz
    path(
        "teacher/quizzes/<int:quiz_id>/delete/", 
        views.delete_quiz, 
        name="delete_quiz"
    ),
    
    # Toggle quiz active/inactive status
    path(
        "teacher/quizzes/<int:quiz_id>/toggle/", 
        views.toggle_quiz_active, 
        name="toggle_quiz_active"
    ),
    
    # Edit quiz settings (timer, due date, etc.)
    path(
        "teacher/quizzes/<int:quiz_id>/settings/", 
        views.edit_quiz_settings, 
        name="edit_quiz_settings"
    ),
    
    # Move quiz to different folder
    path(
        "teacher/quizzes/<int:quiz_id>/move/", 
        views.move_quiz, 
        name="move_quiz"
    ),
    
    
    # =========================================================================
    # TEACHER QUESTION MANAGEMENT ROUTES
    # =========================================================================
    
    # Add new question to quiz
    path(
        "teacher/quizzes/<int:quiz_id>/questions/add/", 
        views.create_question, 
        name="create_question"
    ),
    
    # Edit existing question
    path(
        "teacher/quizzes/<int:quiz_id>/questions/<int:question_id>/edit/", 
        views.edit_question, 
        name="edit_question"
    ),
    
    # Delete question
    path(
        "teacher/quizzes/<int:quiz_id>/questions/<int:question_id>/delete/", 
        views.delete_question, 
        name="delete_question"
    ),
    
    
    # =========================================================================
    # TEACHER SUBMISSION & GRADING ROUTES
    # =========================================================================
    
    # View all submissions for a quiz
    path(
        "teacher/quizzes/<int:quiz_id>/submission/", 
        views.quiz_submissions, 
        name="quiz_submissions"
    ),
    
    # Grade individual submission
    path(
        "teacher/quizzes/<int:quiz_id>/submission/<int:submission_id>/grade/", 
        views.grade_submission, 
        name="grade_submission"
    ),
    
    # Allow student extra attempt
    path(
        "teacher/quizzes/<int:quiz_id>/allow-extra/<int:student_id>/",
        views.allow_extra_attempt,
        name="allow_extra_attempt",
    ),
    
    # Adjust student's allowed attempts (+1 or -1)
    path(
        "teacher/quizzes/<int:quiz_id>/attempts/<int:student_id>/adjust/",
        views.adjust_attempts,
        name="adjust_attempts",
    ),
    
    # Delete teacher's feedback file from FileSubmission
    path(
        "teacher/file-submission/<int:file_submission_id>/delete-feedback/", 
        views.delete_teacher_file, 
        name="delete_teacher_file"
    ),
    
    # Delete teacher's feedback file from Submission
    path(
        "teacher/submission/<int:submission_id>/delete-feedback/", 
        views.delete_submission_teacher_file, 
        name="delete_submission_teacher_file"
    ),
    
    
    # =========================================================================
    # TEACHER FOLDER MANAGEMENT ROUTES
    # =========================================================================
    
    # Create new subject folder
    path("teacher/folders/create/", views.create_folder, name="create_folder"),
    
    # View folder contents
    path(
        "teacher/folders/<int:folder_id>/", 
        views.folder_detail, 
        name="folder_detail"
    ),
    
    # View folder analytics (AI-powered weak topic identification)
    path(
        "teacher/folders/<int:folder_id>/analytics/", 
        views.folder_analytics, 
        name="folder_analytics"
    ),
    
    # Delete folder
    path(
        "teacher/folders/<int:folder_id>/delete/", 
        views.delete_folder, 
        name="delete_folder"
    ),
    
    
    # =========================================================================
    # TEACHER EXPORT ROUTES (Excel downloads)
    # =========================================================================
    
    # Export single quiz submissions to Excel
    path(
        "teacher/quizzes/<int:quiz_id>/export/",
        views.export_submissions_excel,
        name="export_submissions_excel"
    ),

    # Export quiz as PDF (all questions)
    path(
        "teacher/quizzes/<int:quiz_id>/export-pdf/",
        views.export_quiz_pdf,
        name="export_quiz_pdf"
    ),
    path(
        "teacher/folders/<int:folder_id>/export-boxes/",
        views.export_folder_boxes_excel,
        name="export_folder_boxes_excel"
    ),
    
    # Export individual student's report within a folder
    path(
        "teacher/folders/<int:folder_id>/export/student/<int:student_id>/",
        views.export_student_folder_excel,
        name="export_student_folder_excel",
    ),
    
    
    # =========================================================================
    # STUDENT AUTHENTICATION & DASHBOARD ROUTES
    # =========================================================================
    
    # Student signup
    path("student/signup/", views.student_signup, name="student_signup"),
    
    # Student login
    path("student/login/", views.student_login, name="student_login"),
    
    # Student dashboard - view history and enter quiz codes
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    
    # View detailed submission results
    path(
        "student/submissions/<int:submission_id>/", 
        views.student_submission_detail, 
        name="student_submission_detail"
    ),
    
    
    # =========================================================================
    # PASSWORD RESET ROUTES (Forgot password flow)
    # =========================================================================
    
    # Step 1: Enter email to receive reset link
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="quizzes/auth/password_reset_form.html",
            email_template_name="quizzes/auth/password_reset_email.html",
            subject_template_name="quizzes/auth/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    
    # Step 2: Confirmation that email was sent
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="quizzes/auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    
    # Step 3: Enter new password (from email link)
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="quizzes/auth/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    
    # Step 4: Confirmation that password was changed
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="quizzes/auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    
    
    # =========================================================================
    # PASSWORD CHANGE ROUTES (For logged-in users)
    # =========================================================================
    
    # Change password form
    path("change-password/", views.change_password, name="change_password"),
    
    # Change password success page
    path("change-password/done/", views.change_password_done, name="change_password_done"),
    
    
    # =========================================================================
    # UTILITY & DEBUG ROUTES
    # =========================================================================
    
    # Teacher help bot (AI chat assistant)
    path("teacher/help-bot/", views.teacher_help_bot, name="teacher_help_bot"),
    
    # Email configuration diagnostic (DEBUG mode only)
    path("email-diagnostic/", views.email_diagnostic, name="email_diagnostic"),
    
    # Debug routes (for development)
    path("debug/send-email/", views.test_send_email),
    path("debug/", lambda request: HttpResponse("Debug route is active"), name="debug"),
]
