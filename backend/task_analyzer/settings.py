"""
Django settings for task_analyzer project.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==============================================
# SECURITY CRITICAL CONFIGURATION
# ==============================================
# SECURITY WARNING: keep the secret key used in production secret!
# Use a secret key from environment or a safe default for development.
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'dev-secret-key-change-me'  # TODO: override in production via environment
)

# SECURITY WARNING: don't run with debug turned on in production!
# Default to True for local development; override via environment in production.
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allow common local addresses by default so dev server works out of the box
default_allowed = '127.0.0.1,localhost'
ALLOWED_HOSTS = [
    host.strip() for host in os.getenv('ALLOWED_HOSTS', default_allowed).split(',')
    if host.strip()
]
# ==============================================


# In backend/task_analyzer/settings.py

INSTALLED_APPS = [
    'django.contrib.admin', # <-- UNCOMMENT THIS LINE
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',

    # Local apps
    'tasks', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'task_analyzer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Point to the frontend directory for templates
        'DIRS': [BASE_DIR / 'frontend'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'task_analyzer.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'backend' / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# Tell Django where to look for static files that aren't in an app
STATICFILES_DIRS = [
    BASE_DIR / 'frontend',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    # Use standard Django model permissions for now.
    # For a real public API, you'd use authentication classes.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}