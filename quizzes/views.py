from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from .models import Quiz,Question,Submission,Answer
from .forms import (
    TeacherLoginForm,TeacherSignupForm,QuizForm,QuestionForm,EnterQuizForm
)



def enter_quiz(request):
    form=EnterQuizForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        student_name=form.cleaned_data['student_name'].strip()
        quiz_code=form.cleaned_data['quiz_code'].strip().upper()
        
        quiz=Quiz.objects.filter(code=quiz_code).first()
        if not quiz:
            messages.error(request,'Invalid quiz code')
            return render(request,'quizzes/enter_quiz.html',{'form':form})
        request.session['student_name']=student_name
        return redirect('take_quiz',quiz_code=quiz.code)
    return render(request,'quizzes/enter_quiz.html',{'form':form})

def take_quiz(request,quiz_code):
    quiz=get_object_or_404(Quiz,code=quiz_code.upper())
    questions= quiz.questions.all().order_by("id")
    student_name=request.session.get("student_name","")
    
    if request.method=='POST':
        if not student_name:
            student_name=request.POST.get('student_name','').strip() or "Unknown"
            request.session['student_name']=student_name
        total=questions.count()
        score=0
            
        submission=Submission.objects.create(
            quiz=quiz,
            student_name=student_name,
            score=0,
            total=total,
            )
        for q in questions:
            selected= request.POST.get(f'question_{q.id}')
            selected_int=int(selected) if selected else None
            
            is_correct=(selected_int==q.correct_option)
            if is_correct:
                score +=1
            Answer.objects.create(
                submission=submission,
                question=q,
                selected=selected_int,
                is_correct=is_correct,
                )
        submission.score=score
        submission.save()
        return redirect("quiz_result",quiz_code=quiz.code,submission_id=submission.id)
    return render(request,"quizzes/take_quiz.html",{
    'quiz':quiz,
    'questions':questions,
    'student_name':student_name
    })
                
def quiz_result(request,quiz_code,submission_id):
    quiz=get_object_or_404(Quiz,code=quiz_code.upper())
    submission=get_object_or_404(Submission,id=submission_id,quiz=quiz)
    answers=submission.answers.select_related('question').all().order_by('question__id')
    
    return render(request,"quizzes/quiz_result.html",{
        'quiz':quiz,
        'submission':submission,
        'answers':answers
    
    })
    
def teacher_signup(request):
    if request.user.is_authenticated:
        return redirect("teacher_quizzes")
    form=TeacherSignupForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save(commit=False)
        user.set_password(form.cleaned_data['password1'])
        user.is_staff=True
        user.save()
        
        login(request,user)
        messages.success(request,"Account created successfully.")
        return redirect("teacher_quizzes")
    return render(request,"quizzes/teacher_signup.html",{'form':form})

def teacher_login(request):
    if request.user.is_authenticated:
        return redirect("teacher_quizzes")
    form=TeacherLoginForm(request.POST or None)
    if request.method=='POST'and form.is_valid():
        user=authenticate(
            request,username=form.cleaned_data['username'],password=form.cleaned_data['password']
        )
        if user:
            login(request,user)
            return redirect('teacher_quizzes')
        messages.error(request,"Invalid username and Password")
    return render(request,"quizzes/teacher_login.html",{"form":form})

@login_required
def teacher_quizzes(request):
    quizzes=Quiz.objects.filter(teacher=request.user).order_by("-created_at")
    return render(request,'quizzes/teacher_quizzes.html',{'quizzes':quizzes})

@login_required
def create_quiz(request):
    form=QuizForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        quiz=form.save(commit=False)
        quiz.teacher=request.user
        quiz.save()
        messages.success(request,f"Quiz created code:{quiz.code}")
        return redirect("teacher_quizzes")
    return render(request,"quizzes/create_quiz.html",{'form':form})

@login_required
def create_questions(request,quiz_id):
    quiz=get_object_or_404(Quiz,id=quiz_id,teacher=request.user)
    form=QuestionForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid():
        q=form.save(commit=False)
        q.quiz=quiz
        q.save()
        messages.success(request,"Question added")
        return redirect("teacher_quizzes")
    return render(request,"quizzes/create_question.html",{'quiz':quiz,'form':form})

@login_required
def quiz_submissions(request,quiz_id):
    quiz=get_object_or_404(Quiz,id=quiz_id,teacher=request.user)
    submissions=quiz.submissions.all().order_by('-submitted_at')
    return render(request,'quizzes/quiz_submissions.html',{'quiz':quiz,'submissions':submissions})

@login_required
def delete_quiz(request,quiz_id):
    quiz= get_object_or_404(Quiz,id=quiz_id,teacher=request.user)
    if request.method=='POST':
        quiz.delete()
        messages.success(request,'Quiz deleted')
        return redirect('teacher_quizzes')
    return render(request,'quizzes/confirm_delete.html',{'quiz':quiz})
    

def teacher_logout(request):
    logout(request)
    return redirect('teacher_login')


# Create your views here.
