"""
Django settings for task_analyzer project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# ======================================================
# BASE DIRECTORY
# ======================================================
# /project/backend/task_analyzer/settings.py → parent → task_analyzer → parent → backend → parent → project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ======================================================
# SECURITY CONFIGURATION
# ======================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    '.onrender.com',
    'localhost',
    '127.0.0.1'
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
]


# ======================================================
# INSTALLED APPS
# ======================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',

    # Local apps
    'tasks',
]


# ======================================================
# MIDDLEWARE (WhiteNoise Added)
# ======================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- REQUIRED FOR STATIC ON RENDER
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'task_analyzer.urls'


# ======================================================
# TEMPLATES — serve frontend/index.html
# ======================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend'],  # <-- Your HTML folder
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


# ======================================================
# DATABASE
# ======================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'backend' / 'db.sqlite3',
    }
}


# ======================================================
# AUTH VALIDATORS
# ======================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ======================================================
# INTERNATIONALIZATION
# ======================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ======================================================
# STATIC FILES (STATIC + WHITENOISE + FRONTEND SUPPORT)
# ======================================================

STATIC_URL = '/static/'

# Your raw CSS, JS, images (frontend folder)
STATICFILES_DIRS = [
    BASE_DIR / 'frontend',
]

# For Render deployment
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise storage for compressed cached files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# ======================================================
# DEFAULT FIELD
# ======================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ======================================================
# DRF CONFIG
# ======================================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}
