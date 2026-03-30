from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add your remote database settings, allowed hosts, etc. here
ALLOWED_HOSTS = [
    'court-app-141670575225.us-central1.run.app',
    'localhost',
    '127.0.0.1',
]

# [ACTION REQUIRED] Add this line to fix the 403 CSRF error
CSRF_TRUSTED_ORIGINS = ['https://court-app-141670575225.us-central1.run.app']


# --- Google Cloud Storage Settings ---

# 1. Get the Bucket Name
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME')

# 2. Get the Project ID automatically
GS_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')

STORAGES = {
    # Media (Evidence/Photos)
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "project_id": GS_PROJECT_ID,
            "default_acl": None,
            "querystring_auth": False,
        },
    },
    # Static (CSS/JS)
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# --- Database Settings (from environment variables) ---

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Check if running on Google Cloud Run and adjust the database HOST
# The value of this env var is set in the deploy.yml file
if os.getenv('DJANGO_ENV') == 'remote':
    # When connecting via a Unix socket, HOST is the socket path and PORT must be empty.
    DATABASES['default']['HOST'] = f"/cloudsql/{os.getenv('DB_INSTANCE_CONNECTION_NAME')}"
    DATABASES['default']['PORT'] = ''
