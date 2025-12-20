from django.urls import path 
from . import views

urlpatterns=[
    path("",views.enter_quiz,name="enter_quiz"),
    path("quiz/<str:quiz_code>/",views.take_quiz,name="take_quiz"),
    path("quiz/<str:quiz_code>/result/<int:submission_id>/",views.quiz_result,name="quiz_result"),
    path("logout/",views.teacher_logout,name="teacher_logout"),
    
    path("teacher/signup/",views.teacher_signup,name="teacher_signup"),
    path("teacher/login/",views.teacher_login,name="teacher_login"),
    path("teacher/quizzes/",views.teacher_quizzes,name="teacher_quizzes"),
    path("teacher/quizzes/create/",views.create_quiz,name="create_quiz"),
    path("teacher/quizzes/<int:quiz_id>/questions/add/",views.create_questions,name="create_questions"),
    path("teacher/quizzes/<int:quiz_id>/submission/",views.quiz_submissions,name="quiz_submissions"),
    path("teacher/quizzes/<int:quiz_id>/delete/",views.delete_quiz,name="delete_quiz"),
] 