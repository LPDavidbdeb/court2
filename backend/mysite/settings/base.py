"""
Base Django settings for mysite project.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import sys # NEW: Import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is now the project root (the directory containing manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# NEW: Add BASE_DIR to Python's path so top-level modules can be imported
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# This will be overridden in local.py and remote.py
DEBUG = False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', # Required by django-allauth

    # --- Headless V2 API Additions ---
    'ninja_extra',
    'ninja_jwt',
    'corsheaders',

    'django_extensions',
    'django_bootstrap5',
    'crispy_forms',
    'crispy_bootstrap5',
    'sorl.thumbnail',
    'widget_tweaks',
    'treebeard',
    'tinymce',
    'django_bleach',
    'bootstrap',
    "pgvector.django",


    # django-allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Custom user app
    'users.apps.UsersConfig',

    'photos.apps.PhotosConfig',
    'events.apps.EventsConfig',
    'email_manager.apps.EmailManagerConfig',
    'protagonist_manager.apps.ProtagonistManagerConfig',
    'document_manager.apps.DocumentManagerConfig',
    'pdf_manager.apps.PdfManagerConfig',
    'core.apps.CoreConfig',
    'argument_manager.apps.ArgumentManagerConfig',
    'ai_services.apps.AiServicesConfig',
    "video_manager",
    "googlechat_manager",
    'case_manager',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware', # Disabled to allow PDF iframes in React
    'allauth.account.middleware.AccountMiddleware', # django-allauth middleware
    'core.middleware.SuperuserRequiredMiddleware', # Custom middleware for superuser access
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'templates', 'allauth'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csrf', # Added CSRF processor
            ],
        },
    },
]


WSGI_APPLICATION = 'mysite.wsgi.application'


# Database settings will be handled in local.py and remote.py


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

USE_I18N = True

# USE_TZ = True

TIME_ZONE = 'America/Montreal'
USE_TZ = True
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Media files (user-uploaded content)
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- Security Settings ---
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Custom User Model ---
AUTH_USER_MODEL = 'users.CustomUser'

# --- Crispy Forms Settings ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

TINYMCE_DEFAULT_CONFIG = {
    'height': 360,
    'width': 1120,
    'menubar': 'file edit view insert format tools table help',
    'plugins': 'advlist autolink lists link image charmap print preview anchor table',
    'toolbar': 'undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist | table | forecolor backcolor removeformat | pagebreak | charmap emoticons | fullscreen  preview save print | insertfile image media template link anchor codesample | ltr rtl',
    'toolbar_mode': 'floating',
    'link_list': '/argument_manager/ajax/pdf-quotes-for-tinymce/',
}

# Bleach settings
BLEACH_ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'caption', 'blockquote', 'cite']
BLEACH_ALLOWED_ATTRIBUTES = ['href', 'title', 'style', 'border', 'cellspacing', 'cellpadding', 'width', 'align', 'colspan', 'rowspan', 'data-quote-id', 'data-source']
BLEACH_ALLOWED_STYLES = ['font-family', 'font-weight', 'text-decoration', 'font-variant']
BLEACH_STRIP_TAGS = True
BLEACH_STRIP_COMMENTS = True

# API Keys and Credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY") # Added for google-genai compatibility

# Gmail API Configuration
gmail_creds_filename = os.getenv('GMAIL_API_CREDENTIALS_FILE')
GMAIL_API_CREDENTIALS_FILE = os.path.join(BASE_DIR, gmail_creds_filename) if gmail_creds_filename else None

gmail_token_filename = os.getenv('GMAIL_TOKEN_FILE')
GMAIL_TOKEN_FILE = os.path.join(BASE_DIR, gmail_token_filename) if gmail_token_filename else None

# --- Flickr Accounts Configuration ---
FLICKR_ACCOUNTS = {
    "louisphilippe": {
        "api_key": os.getenv("LOUISPHILIPPE_FLICKR_API_KEY"),
        "api_secret": os.getenv("LOUISPHILIPPE_FLICKR_API_SECRET"),
        "token_cache_file": os.getenv("LOUISPHILIPPE_FLICKR_TOKEN_CACHE_FILE"),
        "description": "Account mixing documents and pictures (louisphilippe.david@gmail.com)",
        "user_id": os.getenv("LOUISPHILIPPE_FLICKR_USER_ID")
    },
    "cchic": {
        "api_key": os.getenv("CCHIC_FLICKR_API_KEY"),
        "api_secret": os.getenv("CCHIC_FLICKR_API_SECRET"),
        "token_cache_file": os.getenv("CCHIC_FLICKR_TOKEN_CACHE_FILE"),
        "description": "Picture-focused account (cchic1@hotmail.com)",
        "user_id": os.getenv("CCHIC_FLICKR_USER_ID")
    }
}

# --- django-allauth settings ---
SITE_ID = 1 # Required by django.contrib.sites

LOGIN_REDIRECT_URL = '/' # Redirect to home page after login
ACCOUNT_LOGOUT_REDIRECT_URL = '/' # Redirect to home page after logout

# Simplified django-allauth settings to get past initial migrations
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
# ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Temporarily set to optional to unblock migrations

# Use console email backend for local development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# --- NinjaJWT Configuration ---
# Use email-based token obtain schema to match allauth's ACCOUNT_LOGIN_METHODS = {'email'}
NINJA_JWT = {
    "TOKEN_OBTAIN_PAIR_INPUT_SCHEMA": "mysite.jwt_schema.EmailTokenObtainPairInputSchema",
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "accept",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
