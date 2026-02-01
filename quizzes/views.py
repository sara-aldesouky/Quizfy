from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from .models import Quiz,Question,Submission,Answer,StudentProfile,SubjectFolder, QuizAttemptPermission
from .forms import (
    TeacherLoginForm,TeacherSignupForm,QuizForm,QuestionForm,EnterQuizForm, StudentSignupForm, StudentLoginForm,FolderForm,MoveQuizForm,QuizSettingsForm,ChangePasswordForm
)
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import difflib
import re
from django.db import transaction
from django.utils import timezone
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
import qrcode
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def student_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and not u.is_staff and hasattr(u, "student_profile"),
        login_url="/student/login/"
    )(view_func)

def staff_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url="/teacher/login/"
    )(view_func)


def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("teacher_quizzes")
        return redirect("student_dashboard")
    return render(request, "quizzes/landing.html")


def landing(request):
    """Render the public landing page without redirecting authenticated users.
    This lets the logo/home link always go to the marketing landing page.
    """
    return render(request, "quizzes/landing.html")

def quiz_scan(request, quiz_code):
    """Handle QR code scan - redirect to quiz after checking if student is logged in."""
    logger.info(f"quiz_scan called with quiz_code: {quiz_code}")
    quiz_code = quiz_code.upper()
    quiz = get_object_or_404(Quiz, code=quiz_code)
    
    # If student is logged in, take them directly to the quiz
    if request.user.is_authenticated and hasattr(request.user, "student_profile"):
        logger.info("User is authenticated and has a student profile. Redirecting to quiz.")
        return redirect("take_quiz", quiz_code=quiz_code)
    
    # If not logged in, redirect to student login with the quiz URL as next
    logger.info("User not authenticated. Redirecting to login.")
    from django.urls import reverse
    quiz_url = reverse("take_quiz", kwargs={"quiz_code": quiz_code})
    return redirect(f"{reverse('student_login')}?next={quiz_url}")


@staff_required
def quiz_qr_code(request, quiz_code):
    """Generate and serve a QR code image for a quiz."""
    quiz = get_object_or_404(Quiz, code=quiz_code.upper(), teacher=request.user)
    
    try:
        # Build absolute URL for QR code (works when scanned on mobile)
        protocol = "https" if request.is_secure() else "http"
        domain = request.get_host()
        qr_data = f"{protocol}://{domain}/quiz/{quiz.code}/scan/"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Serve as PNG
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type="image/png")
    except Exception as e:
        # Return a blank 1x1 pixel if generation fails
        return HttpResponse(bytes.fromhex("89504e470d0a1a0a0000000d494844520000000100000001080202000090773db30000000c49444154785e6300010000050001000b0b80c30000000049454e44ae426082"), content_type="image/png")




# --- Teacher Help Bot (FAQ + fuzzy match) ---

TEACHER_KB = [
    {
        "tags": ["create folder", "subject folder", "add subject", "new folder", "folder"],
        "q": "How do I create a subject folder?",
        "a": (
            "Go to **My Subjects** → click **+ Create Subject Folder** → type the subject name (e.g., Physics) → Save.\n\n"
            "After that, you can move quizzes into it using **Move** on any quiz."
        )
    },
    {
        "tags": ["move quiz", "assign quiz", "put quiz in folder", "organize quizzes", "ungrouped"],
        "q": "How do I move a quiz into a folder?",
        "a": (
            "On the teacher dashboard, find the quiz (especially under **Ungrouped Quizzes**) → click **Move** → select the folder → Save."
        )
    },
    {
        "tags": ["export", "excel", "download", "submissions file", "xlsx"],
        "q": "How do I export submissions to Excel?",
        "a": (
            "You have two options:\n"
            "1) Export a single quiz: open the quiz card → click **Export Excel**.\n"
            "2) Export a whole subject folder: open the folder card → click **Export Excel**.\n\n"
            "The file includes: student full name, university ID, section, and grades."
        )
    },
    {
        "tags": ["student access", "login", "account required", "solve quiz"],
        "q": "Can students access quizzes without an account?",
        "a": (
            "No. Students must **sign up / log in** first. After logging in, they can enter a quiz code and submit."
        )
    },
    {
        "tags": ["quiz code", "share code", "where is code"],
        "q": "Where do I find the quiz code?",
        "a": (
            "In the quiz card on your dashboard, you’ll see **Code:** (example: ABC123). Share this code with students."
        )
    },
]

def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def _best_answer(message: str) -> str:
    msg = _normalize(message)

    # 1) quick tag hit (high precision)
    for item in TEACHER_KB:
        for t in item["tags"]:
            if _normalize(t) in msg:
                return item["a"]

    # 2) fuzzy match against known questions + tags (handles different wording)
    candidates = []
    for item in TEACHER_KB:
        candidates.append(item["q"])
        candidates.extend(item["tags"])

    best = difflib.get_close_matches(msg, [_normalize(c) for c in candidates], n=1, cutoff=0.55)
    if best:
        best_norm = best[0]
        for item in TEACHER_KB:
            if _normalize(item["q"]) == best_norm:
                return item["a"]
            for t in item["tags"]:
                if _normalize(t) == best_norm:
                    return item["a"]

    # fallback
    return (
        "I can help with:\n"
        "• Creating subject folders\n"
        "• Moving quizzes into folders\n"
        "• Exporting submissions to Excel\n"
        "• Student login/access\n\n"
        "Try asking: **How do I move a quiz into a folder?**"
    )

@staff_required
@require_POST
def teacher_help_bot(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = {}

    message = (data.get("message") or "").strip()
    if not message:
        return JsonResponse({"reply": "Type your question and I’ll help."})

    reply = _best_answer(message)
    return JsonResponse({"reply": reply})


@student_required
def enter_quiz(request):
    form = EnterQuizForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        quiz_code = form.cleaned_data["quiz_code"].strip().upper()

        quiz = Quiz.objects.filter(code=quiz_code).first()
        if not quiz:
            messages.error(request, "Invalid quiz code.")
            return render(request, "quizzes/enter_quiz.html", {"form": form})

        return redirect("take_quiz", quiz_code=quiz_code)

    return render(request, "quizzes/enter_quiz.html", {"form": form})

@staff_required
@require_POST
def allow_extra_attempt(request, quiz_id, student_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    student = get_object_or_404(User, id=student_id)

    perm, _ = QuizAttemptPermission.objects.get_or_create(
        quiz=quiz, student_user=student,
        defaults={"allowed_attempts": 1}
    )
    perm.allowed_attempts += 1
    perm.save()

    messages.success(request, f"Extra attempt allowed for {student.username}.")
    return redirect("quiz_submissions", quiz_id=quiz.id)

@staff_required
def edit_quiz_settings(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

    form = QuizSettingsForm(request.POST or None, instance=quiz)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Quiz settings updated.")
        return redirect("teacher_quiz_detail", quiz_id=quiz.id)

    return render(request, "quizzes/edit_quiz_settings.html", {
        "quiz": quiz,
        "form": form
    })
    
@ensure_csrf_cookie
@student_required
@student_required
def take_quiz(request, quiz_code):
    quiz = get_object_or_404(Quiz, code=quiz_code.upper())

    # ✅ 1) Teacher stopped quiz OR due date passed
    if not quiz.can_start():
        messages.error(request, "This quiz is closed.")
        return redirect("student_dashboard")

    # ✅ 2) Attempt limit (default = 1)
    perm = QuizAttemptPermission.objects.filter(
        quiz=quiz, student_user=request.user
    ).first()
    allowed = perm.allowed_attempts if perm else 1

    attempts_used = Submission.objects.filter(
        quiz=quiz,
        student_user=request.user,
        is_submitted=True
    ).count()

    if attempts_used >= allowed:
        messages.error(request, "You already submitted this quiz.")
        return redirect("student_dashboard")

    questions = quiz.questions.all().order_by("id")

    # ✅ 3) Get or create an in-progress submission (so refresh won’t create new one)
    submission = Submission.objects.filter(
        quiz=quiz,
        student_user=request.user,
        is_submitted=False
    ).order_by("-id").first()

    if not submission:
        sp = request.user.student_profile
        submission = Submission.objects.create(
            quiz=quiz,
            student_user=request.user,
            student_name=f"{sp.first_name} {sp.second_name} {sp.third_name}",
            score=0,
            total=questions.count(),
            started_at=timezone.now(),
            is_submitted=False,
            attempt_no=attempts_used + 1,
        )
    else:
        # ✅ IMPORTANT PATCH: old rows may have started_at = NULL
        if submission.started_at is None:
            submission.started_at = timezone.now()
            submission.save(update_fields=["started_at"])

    # ✅ 4) Timer in minutes -> seconds
    remaining_seconds = None
    if quiz.duration_minutes:
        duration_seconds = quiz.duration_minutes * 60
        elapsed = (timezone.now() - submission.started_at).total_seconds()
        remaining_seconds = max(0, int(duration_seconds - elapsed))

        # ✅ If time is finished (GET or POST), finalize NOW
        if remaining_seconds <= 0:
            return _finalize_submission(request, quiz, submission, questions)

    # ✅ 5) POST = finalize (manual submit OR timer submits the form)
    if request.method == "POST":
        return _finalize_submission(request, quiz, submission, questions)

    # ✅ 6) GET = show quiz
    return render(request, "quizzes/take_quiz.html", {
        "quiz": quiz,
        "questions": questions,
        "remaining_seconds": remaining_seconds,
        "submission": submission,
    })

@transaction.atomic
def _finalize_submission(request, quiz, submission, questions=None):
    # If already submitted, go to result
    if submission.is_submitted:
        return redirect("quiz_result", quiz_code=quiz.code, submission_id=submission.id)

    # Teacher stopped it / due date passed mid-attempt
    if not quiz.can_start():
        from django.contrib import messages
        messages.error(request, "Quiz was closed by the teacher.")
        return redirect("student_dashboard")

    # If questions not provided, load them
    if questions is None:
        questions = quiz.questions.all().order_by("id")

    # Remove old answers (if re-submit happens)
    submission.answers.all().delete()

    score = 0
    total = questions.count()

    for q in questions:
        selected = request.POST.get(f"question_{q.id}")
        selected_int = int(selected) if selected else None

        is_correct = (selected_int == q.correct_option)
        if is_correct:
            score += 1

        Answer.objects.create(
            submission=submission,
            question=q,
            selected=selected_int,
            is_correct=is_correct,
        )

    submission.score = score
    submission.total = total
    submission.is_submitted = True
    submission.submitted_at = timezone.now()
    submission.save()

    return redirect("quiz_result", quiz_code=quiz.code, submission_id=submission.id)

@staff_required
@require_POST
def toggle_quiz_active(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

    if request.method == "POST":
        quiz.is_active = not quiz.is_active
        quiz.save()

    return redirect("teacher_quiz_detail", quiz_id=quiz.id)

@staff_required
@require_POST
def allow_extra_attempt(request, quiz_id, student_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    student = get_object_or_404(User, id=student_id)

    perm, created = QuizAttemptPermission.objects.get_or_create(
        quiz=quiz,
        student_user=student,
        defaults={"allowed_attempts": 1}
    )

    if not created:
        perm.allowed_attempts += 1
        perm.save()

    messages.success(request, f"Extra attempt allowed for {student.username}.")
    return redirect("quiz_submissions", quiz_id=quiz.id)


def quiz_result(request, quiz_code, submission_id):
    quiz = get_object_or_404(Quiz, code=quiz_code)

    # ✅ scope submission to the quiz to avoid mismatches
    submission = get_object_or_404(Submission, id=submission_id, quiz=quiz)

    # ✅ safe student display
    student_name = submission.student_name or ""
    university_id = ""
    section = ""

    if submission.student_user_id:
        try:
            u = submission.student_user
            sp = getattr(u, "student_profile", None)
            if sp:
                student_name = f"{sp.first_name} {sp.second_name} {sp.third_name}".strip() or student_name
                university_id = sp.university_id or ""
                section = sp.section or ""
            else:
                # fallback to username if no profile
                student_name = u.username or student_name
        except User.DoesNotExist:
            pass

    context = {
        "quiz": quiz,
        "submission": submission,
        "student_name": student_name,
        "university_id": university_id,
        "section": section,
    }
    return render(request, "quizzes/quiz_result.html", context)

@transaction.atomic
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
        # if already logged-in teacher, go dashboard; if student, kick them to student dashboard
        if request.user.is_staff:
            return redirect("teacher_quizzes")
        return redirect("student_dashboard")

    form = TeacherLoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user and user.is_staff:
            login(request, user)
            return redirect("teacher_quizzes")
        messages.error(request, "Invalid teacher credentials.")

    return render(request, "quizzes/teacher_login.html", {"form": form})

@staff_required
def teacher_quizzes(request):
    folders = SubjectFolder.objects.filter(teacher=request.user).order_by("name")
    ungrouped = Quiz.objects.filter(teacher=request.user, folder__isnull=True).order_by("-created_at")
    return render(request, "quizzes/teacher_folders.html", {
        "folders": folders,
        "ungrouped": ungrouped,
    })




@staff_required
def create_folder(request):
    form = FolderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        folder = form.save(commit=False)
        folder.teacher = request.user
        folder.save()
        messages.success(request, "Folder created.")
        return redirect("teacher_quizzes")
    return render(request, "quizzes/create_folder.html", {"form": form})

@staff_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(SubjectFolder, id=folder_id, teacher=request.user)
    quizzes = folder.quizzes.all().order_by("-created_at")
    return render(request, "quizzes/folder_detail.html", {
        "folder": folder,
        "quizzes": quizzes,
    })



@staff_required
def create_quiz(request):
    pre_folder_id = request.GET.get("folder")

    form = QuizForm(request.POST or None, teacher=request.user)

    # Preselect folder when opening the page
    if request.method == "GET" and pre_folder_id:
        form.initial["folder"] = pre_folder_id

    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.teacher = request.user
        quiz.save()
        messages.success(request, f"Quiz created. Code: {quiz.code}")

        # if created inside a folder, go back to that folder
        if quiz.folder_id:
            return redirect("folder_detail", quiz.folder_id)

        return redirect("teacher_quizzes")

    return render(request, "quizzes/create_quiz.html", {"form": form})


@staff_required
def create_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    form = QuestionForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        q = form.save(commit=False)
        q.quiz = quiz
        q.save()
        messages.success(request, "Question added.")
        return redirect("teacher_quizzes")

    return render(request, "quizzes/create_question.html", {"quiz": quiz, "form": form})


@staff_required
def quiz_submissions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

    submissions = (
        Submission.objects
        .filter(quiz=quiz, is_submitted=True)
        .select_related("student_user", "student_user__student_profile")
        .order_by("-submitted_at", "-id")
    )

    student_ids = [s.student_user_id for s in submissions if s.student_user_id]

    perms_qs = QuizAttemptPermission.objects.filter(
        quiz=quiz,
        student_user_id__in=student_ids
    ).values("student_user_id", "allowed_attempts")

    attempt_map = {p["student_user_id"]: p["allowed_attempts"] for p in perms_qs}

    return render(request, "quizzes/quiz_submissions.html", {
        "quiz": quiz,
        "submissions": submissions,
        "attempt_map": attempt_map,
    })
   
@staff_required
@require_POST
def adjust_attempts(request, quiz_id, student_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    student = get_object_or_404(User, id=student_id)

    try:
        delta = int(request.POST.get("delta", "0"))
    except ValueError:
        delta = 0

    if delta not in (-1, 1):
        messages.error(request, "Invalid attempt change.")
        return redirect("quiz_submissions", quiz_id=quiz.id)

    perm, _ = QuizAttemptPermission.objects.get_or_create(
        quiz=quiz,
        student_user=student,
        defaults={"allowed_attempts": 1}
    )

    new_val = perm.allowed_attempts + delta
    if new_val < 1:
        new_val = 1  # ✅ never allow 0 or negative

    perm.allowed_attempts = new_val
    perm.save()

    messages.success(request, f"Allowed attempts updated to {new_val} for {student.username}.")
    return redirect("quiz_submissions", quiz_id=quiz.id)
 

@staff_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz deleted.")
        return redirect("teacher_quizzes")

    return render(request, "quizzes/confirm_delete.html", {"quiz": quiz})


def teacher_logout(request):
    logout(request)
    return redirect('teacher_login')

@transaction.atomic
def student_signup(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    form = StudentSignupForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save()

            StudentProfile.objects.create(
                user=user,
                first_name=form.cleaned_data["first_name"],
                second_name=form.cleaned_data["second_name"],
                third_name=form.cleaned_data["third_name"],
                university_id=form.cleaned_data["university_id"],
                city=form.cleaned_data["city"],
                major=form.cleaned_data["major"],
            )

            login(request, user)
            messages.success(request, "Student account created successfully.")
            return redirect("student_dashboard")

        messages.error(request, "Signup failed. Please fix the errors below.")

    return render(request, "quizzes/student_signup.html", {"form": form})


def student_login(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    form = StudentLoginForm(request, data=request.POST or None)
    next_url = request.GET.get("next", None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()

            # ✅ Keep teacher accounts out of student login
            if user.is_staff:
                messages.error(request, "This login is for students only.")
                return render(request, "quizzes/student_login.html", {"form": form})

            login(request, user)
            
            # Redirect to next URL if provided and safe, otherwise to dashboard
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect("student_dashboard")

        messages.error(request, "Invalid University ID or password.")

    return render(request, "quizzes/student_login.html", {"form": form})


@student_required
def student_dashboard(request):
    profile = request.user.student_profile

    # show history
    submissions = (
        Submission.objects
        .filter(student_user=request.user)
        .select_related("quiz")
        .order_by("-submitted_at")
    )

    # quiz code form on dashboard
    form = EnterQuizForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        quiz_code = form.cleaned_data["quiz_code"].strip().upper()
        quiz = Quiz.objects.filter(code=quiz_code).first()
        if not quiz:
            messages.error(request, "Invalid quiz code.")
        else:
            return redirect("take_quiz", quiz_code=quiz.code)

    return render(request, "quizzes/student_dashboard.html", {
        "profile": profile,
        "submissions": submissions,
        "form": form,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Submission

@student_required
def student_submission_detail(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related("quiz", "student_user").prefetch_related("answers__question"),
        id=submission_id,
        student_user=request.user,  
    )

    answers = submission.answers.select_related("question").all().order_by("question__id")

    return render(request, "quizzes/student_submission_detail.html", {
        "submission": submission,
        "quiz": submission.quiz,
        "answers": answers,
    })



def app_logout(request):
    logout(request)
    return redirect("home")

@staff_required
def move_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    form = MoveQuizForm(request.POST or None, teacher=request.user)

    if request.method == "POST" and form.is_valid():
        quiz.folder = form.cleaned_data["folder"]
        quiz.save()
        messages.success(request, "Quiz moved successfully.")
        return redirect("teacher_quizzes")

    return render(request, "quizzes/move_quiz.html", {
        "quiz": quiz,
        "form": form
    })
def _teacher_required(user):
    return user.is_authenticated and user.is_staff


@login_required
def teacher_quiz_detail(request, quiz_id):
    if not request.user.is_staff:
        return redirect("home")

    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    questions = quiz.questions.order_by("id")

    return render(
        request,
        "quizzes/teacher_quiz_detail.html",
        {"quiz": quiz, "questions": questions},
    )


@login_required
def edit_question(request, quiz_id, question_id):
    if not request.user.is_staff:
        return redirect("home")

    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)

    form = QuestionForm(request.POST or None, request.FILES or None, instance=question)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Question updated successfully.")
        return redirect("teacher_quiz_detail", quiz_id=quiz.id)

    return render(
        request,
        "quizzes/edit_question.html",
        {"quiz": quiz, "question": question, "form": form},
    )


@login_required
def delete_question(request, quiz_id, question_id):
    if not request.user.is_staff:
        return redirect("home")

    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)

    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted.")
        return redirect("teacher_quiz_detail", quiz_id=quiz.id)

    return render(
        request,
        "quizzes/delete_question_confirm.html",
        {"quiz": quiz, "question": question},
    )
    
@staff_required
def edit_quiz_settings(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    form = QuizSettingsForm(request.POST or None, instance=quiz)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Quiz settings updated.")
        return redirect("teacher_quiz_detail", quiz_id=quiz.id)

    return render(request, "quizzes/edit_quiz_settings.html", {
        "quiz": quiz,
        "form": form
    })

# ---------------------------
# HELPERS
# ---------------------------
def _latest_per_student(subs_queryset):
    """
    Keep latest submission per student for a quiz.
    Key: student_user_id if exists, else student_name.
    """
    latest = {}
    for s in subs_queryset.order_by("-submitted_at", "-id"):
        key = s.student_user_id or (s.student_name or "").strip().lower()
        if key and key not in latest:
            latest[key] = s
    return list(latest.values())


def _student_info(submission):
    """
    Returns: (full_name, university_id)
    """
    full_name = (submission.student_name or "").strip()
    university_id = ""

    u = getattr(submission, "student_user", None)
    sp = getattr(u, "student_profile", None) if u else None

    if sp:
        full_name = " ".join(filter(None, [sp.first_name, sp.second_name, sp.third_name])).strip() or full_name
        university_id = getattr(sp, "university_id", "") or ""

    return full_name, university_id



def _autosize(ws, max_width=45):
    for col in range(1, ws.max_column + 1):
        letter = get_column_letter(col)
        max_len = 0
        for cell in ws[letter]:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[letter].width = min(max_len + 2, max_width)


def _apply_table(ws, start_row, end_row, end_col, table_name):
    ref = f"A{start_row}:{get_column_letter(end_col)}{end_row}"
    table = Table(displayName=table_name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium9",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(table)


def _safe_table_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in name)
    if cleaned and cleaned[0].isdigit():
        cleaned = "T_" + cleaned
    return cleaned[:50]



@staff_required
def export_submissions_excel(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

    submissions = (
        Submission.objects
        .filter(quiz=quiz, is_submitted=True)
        .select_related("student_user", "student_user__student_profile")
        .order_by("-submitted_at", "-id")
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Submissions"

      


        


    # ---------------------------
    # Styles (MATCH Student Report)
    # ---------------------------
    dark_title_fill = PatternFill("solid", fgColor="111827")   # very dark
    dark_bar_fill = PatternFill("solid", fgColor="1F2937")     # dark gray
    blue_header_fill = PatternFill("solid", fgColor="2563EB")  # bright blue

    title_font = Font(size=18, bold=True, color="FFFFFF")
    subtitle_font = Font(size=10, color="FFFFFF")
    header_font = Font(bold=True, color="FFFFFF")

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    thin = Side(style="thin", color="D1D5DB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ---------------------------
    # Row 1: Big Title Bar
    # ---------------------------
    ws.merge_cells("A1:F1")
    ws["A1"] = "Quiz Submissions Report"
    ws["A1"].font = title_font
    ws["A1"].alignment = center
    ws["A1"].fill = dark_title_fill
    ws.row_dimensions[1].height = 30

    # ---------------------------
    # Row 2: Subtitle Bar
    # ---------------------------
    ws.merge_cells("A2:F2")
    ws["A2"] = (
        f"Quiz: {quiz.title}  |  Code: {quiz.code}  |  "
        f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}  |  Teacher: {request.user.username}"
    )
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = center
    ws["A2"].fill = dark_bar_fill
    ws.row_dimensions[2].height = 18

    # spacer row
    ws.append([])

    # ---------------------------
    # Table Header Row (Blue)
    # ---------------------------
    headers = [
        "Student Full Name",
        "University ID",
        "Score",
        "Total",
        "Percentage",
        "Submitted At",
    ]

    ws.append(headers)
    header_row = ws.max_row

    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=header_row, column=c)
        cell.font = header_font
        cell.fill = blue_header_fill
        cell.alignment = center
        cell.border = border

    # ---------------------------
    # Data Rows
    # ---------------------------
    start_data_row = header_row + 1

    for s in submissions:
        full_name, university_id = _student_info(s)
        score = int(s.score or 0)
        total = int(s.total or 0)
        pct = (score / total) if total else 0
        submitted_str = s.submitted_at.strftime("%Y-%m-%d %H:%M") if s.submitted_at else ""

        ws.append([
            full_name,
            university_id,
            score,
            total,
            pct,
            submitted_str,
        ])

    end_row = ws.max_row

    # Borders + percentage format
    for r in range(start_data_row, end_row + 1):
        ws.cell(row=r, column=5).number_format = "0.0%"
        for c in range(1, len(headers) + 1):
            ws.cell(row=r, column=c).border = border
            ws.cell(row=r, column=c).alignment = left if c in (1,) else center

    # Excel Table style (filters + stripes)
    if end_row >= start_data_row:
        ref = f"A{header_row}:F{end_row}"
        table = Table(displayName=f"QuizSubs{quiz.id}", ref=ref)
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        ws.add_table(table)

    # Freeze under header
    ws.freeze_panes = f"A{start_data_row}"

    _autosize(ws, max_width=45)


    filename = f"{quiz.code}_submissions_report.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response



# =========================================================
# EXPORT 3: FOLDER BOXES EXPORT (one box per quiz, per-question columns)
# URL: teacher/folders/<folder_id>/export-boxes/
# name="export_folder_boxes_excel"
# =========================================================
@staff_required
def export_folder_boxes_excel(request, folder_id):
    folder = get_object_or_404(SubjectFolder, id=folder_id, teacher=request.user)

    quizzes = (
        Quiz.objects
        .filter(folder=folder, teacher=request.user)
        .order_by("created_at")
    )

    all_subs = (
        Submission.objects
        .filter(quiz__in=quizzes, is_submitted=True)
        .select_related("quiz", "student_user", "student_user__student_profile")
        .prefetch_related("answers__question")
        .order_by("-submitted_at", "-id")
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Folder Boxes"

    # Styles
    title_font = Font(size=16, bold=True, color="FFFFFF")
    title_fill = PatternFill("solid", fgColor="111827")

    section_font = Font(size=12, bold=True, color="FFFFFF")
    section_fill = PatternFill("solid", fgColor="1F2937")

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E79")

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    thin = Side(style="thin", color="D1D5DB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Header
    ws.merge_cells("A1:Z1")
    ws["A1"] = f"Subject Folder Boxes Report — {folder.name}"
    ws["A1"].font = title_font
    ws["A1"].fill = title_fill
    ws["A1"].alignment = center
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:Z2")
    ws["A2"] = f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')} | Teacher: {request.user.username}"
    ws["A2"].alignment = center
    ws["A2"].fill = section_fill
    ws["A2"].font = Font(size=10, color="FFFFFF")
    ws.row_dimensions[2].height = 18

    row = 4

    for q in quizzes:
        questions = list(q.questions.all().order_by("id"))
        q_headers = [f"Q{i}" for i in range(1, len(questions) + 1)]

        headers = [
            "Student Full Name", "University ID", 
            "Score", "Total", "Percentage"
        ] + q_headers

        end_col = len(headers)

        # Box title row
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=end_col)
        tcell = ws.cell(row=row, column=1, value=f"{q.title}   (Code: {q.code})")
        tcell.font = section_font
        tcell.fill = section_fill
        tcell.alignment = left
        row += 1

        # Header row
        for c, h in enumerate(headers, start=1):
            hc = ws.cell(row=row, column=c, value=h)
            hc.font = header_font
            hc.fill = header_fill
            hc.alignment = center
            hc.border = border

        header_row = row
        row += 1

        # Latest submissions per student
        q_subs = all_subs.filter(quiz=q)
        latest = _latest_per_student(q_subs)
        latest.sort(key=lambda s: (_student_info(s)[0] or "").lower())

        start_data_row = row

        for s in latest:
            full_name, university_id = _student_info(s)
            score = int(s.score or 0)
            total = int(s.total or 0)
            pct = (score / total) if total else 0

            # per-question correctness: 1 correct, 0 wrong, "" missing
            ans_map = {a.question_id: (1 if a.is_correct else 0) for a in s.answers.all()}
            per_q = [ans_map.get(qq.id, "") for qq in questions]

            values = [full_name, university_id, score, total, pct] + per_q

            for c, v in enumerate(values, start=1):
                dc = ws.cell(row=row, column=c, value=v)
                dc.border = border
                dc.alignment = center if c >= 4 else left

            ws.cell(row=row, column=5).number_format = "0.00%"

            row += 1

        end_row = row - 1

        # Table styling
        if end_row >= start_data_row:
            ref = f"A{header_row}:{get_column_letter(end_col)}{end_row}"
            table_name = _safe_table_name(f"Quiz_{q.id}_{q.code}")
            table = Table(displayName=table_name, ref=ref)
            table.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium9",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False,
            )
            ws.add_table(table)

        row += 2

    ws.freeze_panes = "A4"
    _autosize(ws, max_width=35)

    filename = f"{folder.name}_BOXES_report.xlsx".replace(" ", "_")
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

# ---------------------------
# Autosize helper
# ---------------------------
def _autosize_columns(ws, max_width=45):
    for col in range(1, ws.max_column + 1):
        letter = get_column_letter(col)
        max_len = 0
        for cell in ws[letter]:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[letter].width = min(max_len + 2, max_width)


@staff_required
def export_student_folder_excel(request, folder_id, student_id):
    folder = get_object_or_404(SubjectFolder, id=folder_id, teacher=request.user)
    student = get_object_or_404(User, id=student_id)

    quizzes = (
        Quiz.objects
        .filter(folder=folder, teacher=request.user)
        .order_by("created_at")
    )

    submissions = (
        Submission.objects
        .filter(quiz__in=quizzes, student_user=student, is_submitted=True)
        .select_related("quiz", "student_user", "student_user__student_profile")
        .order_by("quiz__title", "-submitted_at", "-id")
    )

    sp = getattr(student, "student_profile", None)

    wb = Workbook()
    ws = wb.active
    ws.title = "Student Report"

    # ------------------------------------------------------------
    # Column widths (match the clean look)
    # ------------------------------------------------------------
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 32
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 22

    # ------------------------------------------------------------
    # Styles (matching your screenshot)
    # ------------------------------------------------------------
    dark_title_fill = PatternFill("solid", fgColor="111827")   # very dark
    dark_bar_fill = PatternFill("solid", fgColor="1F2937")     # dark gray
    blue_header_fill = PatternFill("solid", fgColor="2563EB")  # bright blue

    title_font = Font(size=18, bold=True, color="FFFFFF")
    subtitle_font = Font(size=10, color="FFFFFF")
    section_font = Font(size=12, bold=True, color="FFFFFF")
    header_font = Font(bold=True, color="FFFFFF")

    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    thin = Side(style="thin", color="D1D5DB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ------------------------------------------------------------
    # Row 1: Big Title
    # ------------------------------------------------------------
    ws.merge_cells("A1:F1")
    ws["A1"] = "Student Performance Report"
    ws["A1"].font = title_font
    ws["A1"].alignment = center
    ws["A1"].fill = dark_title_fill
    ws.row_dimensions[1].height = 30

    # ------------------------------------------------------------
    # Row 2: Subtitle bar (Subject Folder + Generated)
    # ------------------------------------------------------------
    ws.merge_cells("A2:F2")
    ws["A2"] = f"Subject Folder: {folder.name}   |   Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}"
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = center
    ws["A2"].fill = dark_bar_fill
    ws.row_dimensions[2].height = 18

    # ------------------------------------------------------------
    # Student Info section header
    # ------------------------------------------------------------
    ws.merge_cells("A4:F4")
    ws["A4"] = "Student Info"
    ws["A4"].font = section_font
    ws["A4"].alignment = Alignment(horizontal="left", vertical="center")
    ws["A4"].fill = dark_bar_fill
    ws.row_dimensions[4].height = 18

    bold = Font(bold=True)

    # Student info rows (like screenshot)
    info_rows = [
        ("Student Full Name", f"{sp.first_name} {sp.second_name} {sp.third_name}".strip() if sp else student.username),
        ("University ID", sp.university_id if sp else ""),
        ("City", sp.city if sp else ""),
        ("Major", sp.get_major_display() if sp else ""),
    ]

    r = 5
    for label, value in info_rows:
        ws[f"A{r}"] = label
        ws[f"B{r}"] = value
        ws[f"A{r}"].font = bold

        # borders (only A+B like screenshot)
        for c in range(1, 3):
            ws.cell(row=r, column=c).border = border
            ws.cell(row=r, column=c).alignment = left

        r += 1

    # ------------------------------------------------------------
    # Quiz Results section header
    # ------------------------------------------------------------
    start_table = r + 1
    ws.merge_cells(f"A{start_table}:F{start_table}")
    ws[f"A{start_table}"] = "Quiz Results (This Folder)"
    ws[f"A{start_table}"].font = section_font
    ws[f"A{start_table}"].alignment = Alignment(horizontal="left", vertical="center")
    ws[f"A{start_table}"].fill = dark_bar_fill
    ws.row_dimensions[start_table].height = 18

    # ------------------------------------------------------------
    # Table header row (blue)
    # ------------------------------------------------------------
    headers_row = start_table + 1
    headers = ["Quiz Title", "Quiz Code", "Score", "Total", "Percentage", "Submitted At"]

    for i, h in enumerate(headers, start=1):
        cell = ws.cell(row=headers_row, column=i, value=h)
        cell.font = header_font
        cell.fill = blue_header_fill
        cell.alignment = center
        cell.border = border

    # latest attempt per quiz (one row per quiz)
    latest = {}
    for s in submissions:
        if s.quiz_id not in latest:
            latest[s.quiz_id] = s

    ordered = sorted(latest.values(), key=lambda x: (x.quiz.title or "").lower())

    data_row = headers_row + 1

    total_score = 0
    total_total = 0

    for s in ordered:
        score = int(s.score or 0)
        tot = int(s.total or 0)
        pct = (score / tot) if tot else 0
        submitted_str = s.submitted_at.strftime("%Y-%m-%d %H:%M") if s.submitted_at else ""

        total_score += score
        total_total += tot

        row_values = [s.quiz.title, s.quiz.code, score, tot, pct, submitted_str]

        for col_idx, val in enumerate(row_values, start=1):
            cell = ws.cell(row=data_row, column=col_idx, value=val)
            cell.border = border
            cell.alignment = left if col_idx in (1, 6) else center

        ws.cell(row=data_row, column=5).number_format = "0.0%"
        data_row += 1

    last_data_row = data_row - 1

    # Add Excel “Table” styling like screenshot filters
    if last_data_row >= headers_row + 1:
        table_ref = f"A{headers_row}:F{last_data_row}"
        table = Table(displayName="StudentQuizResults", ref=table_ref)
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        ws.add_table(table)

    # Freeze panes under table header
    ws.freeze_panes = f"A{headers_row+1}"

    # Optional autosize
    _autosize_columns(ws, max_width=45)

    filename = f"{folder.name}_{sp.university_id if sp else student.id}_report.xlsx".replace(" ", "_")
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
def quiz_status(request, quiz_code):
    quiz = get_object_or_404(Quiz, code=quiz_code)
    return JsonResponse({"active": bool(quiz.is_active)})
@staff_member_required
def send_test_email(request):
    to_email = request.user.email
    if not to_email:
        messages.error(request, "Your teacher account has no email saved in User.email.")
        return redirect("teacher_quizzes")

    try:
        send_mail(
            subject="Quizfy SMTP Test ✅",
            message="If you received this, Render + Gmail SMTP works.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        messages.success(request, f"Test email sent to {to_email}. Check inbox/spam.")
    except Exception as e:
        messages.error(request, f"SMTP failed: {e}")
    return redirect("teacher_quizzes")
def test_send_email(request):
    send_mail(
        subject="Quizfy Test Email",
        message="Hello! This is a test from Quizfy via SendGrid.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["YOUR_PERSONAL_EMAIL@gmail.com"],
        fail_silently=False,
    )
    return HttpResponse("Sent (check logs + inbox)")


# ============================================================
# PASSWORD CHANGE FOR LOGGED-IN USERS (Email Verification)
# ============================================================

@login_required
def change_password(request):
    """
    View for logged-in users to change their password.
    Requires old password verification.
    """
    form = ChangePasswordForm(request.user, request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your password has been changed successfully!")
        return redirect("change_password_done")
    
    return render(request, "quizzes/change_password.html", {"form": form})


@login_required
def change_password_done(request):
    """
    Confirmation page after password change.
    """
    return render(request, "quizzes/change_password_done.html")