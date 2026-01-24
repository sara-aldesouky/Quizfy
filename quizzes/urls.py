from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("teacher/help-bot/", views.teacher_help_bot, name="teacher_help_bot"),

    path("quiz/<str:quiz_code>/", views.take_quiz, name="take_quiz"),
    path("quiz/<str:quiz_code>/result/<int:submission_id>/", views.quiz_result, name="quiz_result"),

    path("logout/", views.app_logout, name="app_logout"),

    # Teacher auth + quizzes
    path("teacher/signup/", views.teacher_signup, name="teacher_signup"),
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    path("teacher/quizzes/", views.teacher_quizzes, name="teacher_quizzes"),
    path("teacher/quizzes/create/", views.create_quiz, name="create_quiz"),
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




]
