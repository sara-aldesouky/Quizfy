from django.db import models
from django.contrib.auth.models import User
import secrets

def question_image_upload_path(instance, filename):
    return f'quiz_images/quiz_{instance.quiz.id}/{filename}'
    

class Quiz(models.Model):
    title=models.CharField(max_length=60)
    code=models.CharField(max_length=40,unique=True,blank=True,null=True)
    teacher=models.ForeignKey(User, on_delete=models.CASCADE,related_name='quizzes')
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        if not self.code:
            self.code=secrets.token_hex(3).upper()
        super().save(*args,**kwargs)

    def __str__(self):
        return f'{self.title} - {self.code}'

class Question(models.Model):
    quiz=models.ForeignKey(Quiz,on_delete=models.CASCADE,related_name='questions')
    text=models.TextField(blank=True)
    image=models.ImageField(upload_to=question_image_upload_path, blank=True , null=True)
    option1=models.CharField(max_length=60)
    option2=models.CharField(max_length=60)
    option3=models.CharField(max_length=60)
    option4=models.CharField(max_length=60)
    correct_option=models.IntegerField(choices=[
        (1,'Option 1'),(2,'Option 2'),(3,'Option 3'),(4,'Option 4')
    ])
    def option_text(self,number):
        return {
            1:self.option1,
            2:self.option2,
            3:self.option3,
            4:self.option4,
        }.get(number,"(blank)")               

    def __str__(self):
        return self.text[:60] if self.text else f"Question {self.id}"

class Submission(models.Model):
    quiz=models.ForeignKey(Quiz,on_delete=models.CASCADE, related_name='submissions')
    student_name=models.CharField(max_length=60)
    score=models.IntegerField()
    total=models.IntegerField()
    submitted_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.quiz.code} ({self.score}/{self.total})"
class Answer(models.Model):
    submission=models.ForeignKey(Submission,on_delete=models.CASCADE,related_name='answers')
    question=models.ForeignKey(Question,on_delete=models.CASCADE)
    selected=models.IntegerField(null=True,blank=True)
    is_correct=models.BooleanField(default=False)

# Create your models here.
