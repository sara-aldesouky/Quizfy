from django.contrib import admin
from .models import Quiz,Question,Submission,Answer

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Submission)
admin.site.register(Answer)

# Register your models here.
