# quizzes/forms.py

import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Quiz, Question, StudentProfile, SubjectFolder


class TeacherLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class QuizSettingsForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["due_at", "duration_minutes", "is_active"]

        widgets = {
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "duration_minutes": forms.NumberInput(attrs={
                "type": "number",
                "min": 1,
                "placeholder": "e.g. 15"
            }),
        }
class TeacherSignupForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned



class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "folder"]  # ✅ folder exists in Quiz model

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        self.fields["title"].widget.attrs.update({"placeholder": "Quiz title"})

        # If you want teacher-specific folders only:
        if teacher:
            self.fields["folder"].queryset = teacher.folders.all()

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            "text",
            "image",
            "option1",
            "option2",
            "option3",
            "option4",
            "correct_option",
        ]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3}),
        }


class EnterQuizForm(forms.Form):
    quiz_code = forms.CharField(
        max_length=10,
        label="Quiz Code",
        widget=forms.TextInput(attrs={"placeholder": "Enter quiz code"}),
    )


def slugify_simple(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[^a-z0-9]", "", value)
    return value

class StudentSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=60)
    second_name = forms.CharField(max_length=60)
    third_name = forms.CharField(max_length=60)

    university_id = forms.CharField(max_length=30)

    city = forms.ChoiceField(choices=StudentProfile.CITY_CHOICES)
    major = forms.ChoiceField(choices=StudentProfile.MAJOR_CHOICES)

    email = forms.EmailField()

    class Meta:
        model = User
        fields = (
            "first_name",
            "second_name",
            "third_name",
            "university_id",
            "city",
            "major",
            "email",
            "password1",
            "password2",
        )

    def clean_university_id(self):
        uni_id = self.cleaned_data["university_id"]
        if StudentProfile.objects.filter(university_id=uni_id).exists():
            raise forms.ValidationError("University ID already exists.")
        return uni_id

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def _generate_username(self, base: str) -> str:
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            counter += 1
            username = f"{base}{counter}"
        return username

    def save(self, commit=True):
        user = super().save(commit=False)

        first = self.cleaned_data["first_name"]
        second = self.cleaned_data["second_name"]
        third = self.cleaned_data["third_name"]
        uni_id = self.cleaned_data["university_id"]

        base_username = slugify_simple(f"{first}{second}{third}{uni_id[-3:]}")
        user.username = self._generate_username(base_username)

        user.first_name = first
        user.last_name = f"{second} {third}"
        user.email = self.cleaned_data["email"].lower()
        user.is_staff = False

        if commit:
            user.save()

        return user

class FolderForm(forms.ModelForm):
    class Meta:
        model = SubjectFolder
        fields = ["name"]


class MoveQuizForm(forms.Form):
    folder = forms.ModelChoiceField(
        queryset=SubjectFolder.objects.none(),
        required=False,
        empty_label="— Ungrouped —",
        label="Move to folder",
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        if teacher:
            self.fields["folder"].queryset = SubjectFolder.objects.filter(
                teacher=teacher
            ).order_by("name")


class StudentLoginForm(AuthenticationForm):
    """
    Allows login using username OR email.
    The field name stays 'username' because AuthenticationForm expects it.
    """

    def clean_username(self):
        identifier = (self.cleaned_data.get("username") or "").strip()

        # If user typed an email, translate it to the real username
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                return user.username

        return identifier