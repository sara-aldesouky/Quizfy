from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.http import HttpResponse


urlpatterns = [
    path("", views.home, name="home"),
    path("landing/", views.landing, name="landing"),
    path("teacher/help-bot/", views.teacher_help_bot, name="teacher_help_bot"),
    path("email-diagnostic/", views.email_diagnostic, name="email_diagnostic"),

    # More specific quiz patterns first
    path("quiz/<str:quiz_code>/result/<int:submission_id>/", views.quiz_result, name="quiz_result"),
    path("quiz/<str:quiz_code>/qr/", views.quiz_qr_code, name="quiz_qr_code"),
    path("quiz/<str:quiz_code>/join/", views.quiz_join, name="quiz_join"),
    path("quiz/<str:quiz_code>/scan/", views.quiz_scan_redirect, name="quiz_scan_redirect"),
    # Generic quiz pattern last
    path("quiz/<str:quiz_code>/", views.take_quiz, name="take_quiz"),

    path("logout/", views.app_logout, name="app_logout"),

    # Teacher auth + quizzes
    path("teacher/signup/", views.teacher_signup, name="teacher_signup"),
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    path("teacher/quizzes/", views.teacher_quizzes, name="teacher_quizzes"),
    path("teacher/quizzes/create/", views.create_quiz, name="create_quiz"),
    path("teacher/quizzes/live-counts/", views.quiz_live_counts, name="quiz_live_counts"),
    path("teacher/quizzes/<int:quiz_id>/", views.teacher_quiz_detail, name="teacher_quiz_detail"),
    path("teacher/quizzes/<int:quiz_id>/delete/", views.delete_quiz, name="delete_quiz"),
    path("teacher/quizzes/<int:quiz_id>/toggle/", views.toggle_quiz_active, name="toggle_quiz_active"),
    path("teacher/quizzes/<int:quiz_id>/settings/", views.edit_quiz_settings, name="edit_quiz_settings"),

    # Questions
    path("teacher/quizzes/<int:quiz_id>/questions/add/", views.create_question, name="create_question"),
    path("teacher/quizzes/<int:quiz_id>/questions/<int:question_id>/edit/", views.edit_question, name="edit_question"),
    path("teacher/quizzes/<int:quiz_id>/questions/<int:question_id>/delete/", views.delete_question, name="delete_question"),

    # Submissions + exports (per quiz)
    path("teacher/quizzes/<int:quiz_id>/submission/", views.quiz_submissions, name="quiz_submissions"),
    path("teacher/quizzes/<int:quiz_id>/submission/<int:submission_id>/grade/", views.grade_submission, name="grade_submission"),
    path("teacher/file-submission/<int:file_submission_id>/delete-feedback/", views.delete_teacher_file, name="delete_teacher_file"),
    path("teacher/quizzes/<int:quiz_id>/export/", views.export_submissions_excel, name="export_submissions_excel"),

    # Move quiz
    path("teacher/quizzes/<int:quiz_id>/move/", views.move_quiz, name="move_quiz"),

    # Student
    path("student/signup/", views.student_signup, name="student_signup"),
    path("student/login/", views.student_login, name="student_login"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/submissions/<int:submission_id>/", views.student_submission_detail, name="student_submission_detail"),

    # Folders + exports (per folder)
    path("teacher/folders/create/", views.create_folder, name="create_folder"),
    path("teacher/folders/<int:folder_id>/", views.folder_detail, name="folder_detail"),
    path("teacher/folders/<int:folder_id>/analytics/", views.folder_analytics, name="folder_analytics"),
    path("teacher/folders/<int:folder_id>/delete/", views.delete_folder, name="delete_folder"),
    

    path(
        "teacher/quizzes/<int:quiz_id>/export/",
        views.export_submissions_excel,
        name="export_submissions_excel"
    ),

   
    # Export folder boxes report
    path(
        "teacher/folders/<int:folder_id>/export-boxes/",
        views.export_folder_boxes_excel,
        name="export_folder_boxes_excel"
    ),

    # Optional: export one student within a folder
    path(
    "teacher/folders/<int:folder_id>/export/student/<int:student_id>/",
    views.export_student_folder_excel,
    name="export_student_folder_excel",
),
path(
    "teacher/quizzes/<int:quiz_id>/allow-extra/<int:student_id>/",
    views.allow_extra_attempt,
    name="allow_extra_attempt",
),

path(
    "teacher/quizzes/<int:quiz_id>/attempts/<int:student_id>/adjust/",
    views.adjust_attempts,
    name="adjust_attempts",
),
path("quiz/<str:quiz_code>/status/", views.quiz_status, name="quiz_status"),

# Password reset (Teacher + Student)
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
path(
    "password-reset/done/",
    auth_views.PasswordResetDoneView.as_view(
        template_name="quizzes/auth/password_reset_done.html",
    ),
    name="password_reset_done",
),
path(
    "reset/<uidb64>/<token>/",
    auth_views.PasswordResetConfirmView.as_view(
        template_name="quizzes/auth/password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ),
    name="password_reset_confirm",
),
path(
    "reset/done/",
    auth_views.PasswordResetCompleteView.as_view(
        template_name="quizzes/auth/password_reset_complete.html",
    ),
    name="password_reset_complete",
),

# Password change for logged-in users
path("change-password/", views.change_password, name="change_password"),
path("change-password/done/", views.change_password_done, name="change_password_done"),

path("debug/send-email/", views.test_send_email),
path("debug/", lambda request: HttpResponse("Debug route is active"), name="debug"),



]
