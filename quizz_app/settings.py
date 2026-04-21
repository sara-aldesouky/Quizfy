"""
=============================================================================
Django Settings for Quizfy Project
=============================================================================

This file contains all configuration settings for the Quizfy quiz platform.

ENVIRONMENT VARIABLES (set these in production):
------------------------------------------------
Required:
    - DJANGO_SECRET_KEY    : Secret key for cryptographic signing
    - DJANGO_DEBUG         : "0" for production, "1" for development
    - ALLOWED_HOSTS        : Comma-separated list of allowed hosts
    - DATABASE_URL         : PostgreSQL connection string (for production)

File Storage (Cloudinary):
    - CLOUDINARY_CLOUD_NAME
    - CLOUDINARY_API_KEY
    - CLOUDINARY_API_SECRET

Email (SendGrid preferred):
    - SENDGRID_API_KEY     : For sending emails via SendGrid API
  OR (SMTP fallback):
    - EMAIL_HOST           : SMTP server hostname
    - EMAIL_HOST_USER      : SMTP username
    - EMAIL_HOST_PASSWORD  : SMTP password

Optional:
    - OPENAI_API_KEY       : For AI-powered learning analytics
    - SITE_URL             : Full URL of the site (for password reset links)

Author: Quizfy Team
Last Updated: 2024
=============================================================================
"""

import os
from pathlib import Path

import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api


# =============================================================================
# BASE CONFIGURATION
# =============================================================================

# Base directory of the project (parent of quizz_app folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Security key - MUST be changed in production via environment variable
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key")

# Debug mode - NEVER enable in production
# Set DJANGO_DEBUG="0" in production environment
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"


# =============================================================================
# HOSTS & SECURITY SETTINGS
# =============================================================================

# Parse allowed hosts from environment variable (comma-separated)
ALLOWED_HOSTS_RAW = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = (
    ["*"]
    if ALLOWED_HOSTS_RAW.strip() == "*"
    else [h.strip() for h in ALLOWED_HOSTS_RAW.split(",") if h.strip()]
)

# CSRF trusted origins for Render deployment
# Add your custom domain here if you have one
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]


# =============================================================================
# INSTALLED APPLICATIONS
# =============================================================================

INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",          # Admin interface
    "django.contrib.auth",           # Authentication system
    "django.contrib.contenttypes",   # Content type framework
    "django.contrib.sessions",       # Session framework
    "django.contrib.messages",       # Messaging framework
    "django.contrib.staticfiles",    # Static files handling
    "django.contrib.sites",          # Sites framework (for password reset)
    
    # Third-party apps
    "cloudinary_storage",            # Cloud storage for media files
    "cloudinary",                    # Cloudinary integration
    
    # Project apps
    "quizzes",                       # Main quiz application
]

# Site ID for django.contrib.sites (required for password reset emails)
SITE_ID = 1


# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",        # Security headers
    "whitenoise.middleware.WhiteNoiseMiddleware",           # Serve static files
    "django.contrib.sessions.middleware.SessionMiddleware", # Session handling
    "django.middleware.common.CommonMiddleware",            # Common operations
    "django.middleware.csrf.CsrfViewMiddleware",            # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Auth
    "django.contrib.messages.middleware.MessageMiddleware", # Flash messages
    "django.middleware.clickjacking.XFrameOptionsMiddleware",   # Clickjacking protection
]


# =============================================================================
# URL & WSGI CONFIGURATION
# =============================================================================

ROOT_URLCONF = "quizz_app.urls"           # Main URL configuration module
WSGI_APPLICATION = "quizz_app.wsgi.application"  # WSGI application


# =============================================================================
# TEMPLATE CONFIGURATION
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],                     # Additional template directories
        "APP_DIRS": True,               # Look for templates in app directories
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Uses DATABASE_URL environment variable for production (PostgreSQL)
# Falls back to SQLite for local development
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,  # Keep database connections open for 10 minutes
    )
}


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Riyadh"  # Saudi Arabia timezone
USE_I18N = True            # Enable internationalization
USE_TZ = True              # Use timezone-aware datetimes


# =============================================================================
# STATIC FILES (CSS, JavaScript, images)
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise for efficient static file serving in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


# =============================================================================
# MEDIA FILES (User uploads)
# =============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =============================================================================
# CLOUDINARY CONFIGURATION (Cloud file storage for production)
# =============================================================================

# Cloudinary provides persistent file storage for Render's ephemeral filesystem
# Set these environment variables in your Render dashboard:
# - CLOUDINARY_CLOUD_NAME
# - CLOUDINARY_API_KEY
# - CLOUDINARY_API_SECRET

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
}

# Initialize Cloudinary client
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True  # Always use HTTPS
)

# Use Cloudinary for media files in production only (when credentials are set)
if not DEBUG and CLOUDINARY_STORAGE['CLOUD_NAME']:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# =============================================================================
# AUTHENTICATION SETTINGS
# =============================================================================

# Default URLs for login/logout
# Configured for student access by default
LOGIN_URL = "/student/login/"
LOGIN_REDIRECT_URL = "/student/dashboard/"
LOGOUT_REDIRECT_URL = "/student/login/"


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "redact_secrets": {
            "()": "quizz_app.safe_logging.RedactingFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["redact_secrets"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        # General Django logging
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        # Log request errors at ERROR level only
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Email debugging
        "django.core.mail": {
            "handlers": ["console"],
            "level": os.getenv("MAIL_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        # Keep HTTP client internals from dumping headers in production logs.
        "httpx": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "httpcore": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "openai": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# SendGrid is the preferred email provider (works on Render without issues)
# Set SENDGRID_API_KEY in environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

if SENDGRID_API_KEY:
    # Use SendGrid API backend (bypasses SMTP, more reliable on Render)
    EMAIL_BACKEND = "quizz_app.sendgrid_backend.SendgridBackend"
    SENDGRID_SANDBOX_MODE_IN_DEBUG = False
else:
    # Fallback to SMTP (Brevo/Sendinblue is a good free alternative)
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp-relay.brevo.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    
    # If no SMTP credentials are configured, use console backend
    # This prints emails to the terminal (useful for development)
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Site URL used in password reset emails
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000")

# Default "from" email address for outgoing emails
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_FROM_ADDRESS", "noreply@quizfy.com")


# =============================================================================
# THIRD-PARTY API KEYS
# =============================================================================

# OpenAI API Key for AI-powered learning analytics (optional feature)
# Get your key at: https://platform.openai.com/api-keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# =============================================================================
# MISCELLANEOUS SETTINGS
# =============================================================================

# Default primary key type for auto-generated model IDs
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
