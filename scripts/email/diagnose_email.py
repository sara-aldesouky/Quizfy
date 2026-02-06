#!/usr/bin/env python
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizz_app.settings')

import django
django.setup()

from django.conf import settings

print("\n--- DJANGO EMAIL CONFIGURATION ---\n")

print("EMAIL_BACKEND:", settings.EMAIL_BACKEND)
print("EMAIL_HOST:", settings.EMAIL_HOST)
print("EMAIL_PORT:", settings.EMAIL_PORT)
print("EMAIL_USE_TLS:", settings.EMAIL_USE_TLS)
print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)

pwd = settings.EMAIL_HOST_PASSWORD
if pwd:
    print(f"EMAIL_HOST_PASSWORD: SET (length={len(pwd)} chars)")
else:
    print("EMAIL_HOST_PASSWORD: NOT SET / EMPTY")
    print("  -> Add this environment variable on Render!")

print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)
print("SITE_ID:", getattr(settings, 'SITE_ID', 'NOT SET'))

print("\n--- Testing email send ---\n")
from django.core.mail import send_mail

try:
    result = send_mail(
        subject="Quizfy SMTP Test",
        message="If you see this, email works!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["test@example.com"],
        fail_silently=False,
    )
    print(f"SUCCESS: Email send returned {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

print("\n" + "-"*50)
