from django import forms 
from django.contrib.auth.models import User
from .models import Quiz,Question


class TeacherLoginForm(forms.Form):
    username=forms.CharField()
    password=forms.CharField(widget=forms.PasswordInput)

class TeacherSignupForm(forms.ModelForm):
    password1=forms.CharField(label='Password',widget=forms.PasswordInput)
    password2=forms.CharField(label='Confirm Password',widget=forms.PasswordInput)
    
    class Meta:
        model= User
        fields=['username','email']
        
    def clean(self):
        cleaned=super().clean()
        
        if cleaned.get('password1') != cleaned.get('password2'):
            raise forms.ValidationError('Passwords do not match')
        return cleaned
class QuizForm(forms.ModelForm):
    class Meta:
        model=Quiz
        fields=['title']
class QuestionForm(forms.ModelForm):
    class Meta:
        model= Question
        fields=['text','image','option1','option2','option3','option4','correct_option']
        
        widgets={
            'text':forms.Textarea(attrs={'rows':3})
        }
class EnterQuizForm(forms.Form):
    student_name= forms.CharField(max_length=100)
    quiz_code=forms.CharField(max_length=30)
        
        
    
    
