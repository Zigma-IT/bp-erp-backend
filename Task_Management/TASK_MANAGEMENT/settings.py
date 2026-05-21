"""
Django settings for TASK_MANAGEMENT project.
"""

import sys
from pathlib import Path
from corsheaders.defaults import default_headers

# --------------------------------------------------
# BASE DIRECTORY
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MASTERS_DIR = BASE_DIR.parent / "MASTERS"

if str(MASTERS_DIR) not in sys.path:
    sys.path.insert(0, str(MASTERS_DIR))

# --------------------------------------------------
# SECURITY
# --------------------------------------------------

SECRET_KEY = 'django-insecure-task-management-secret-key'

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '0.0.0.0',
]

# --------------------------------------------------
# CORS & CSRF
# --------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5174',
    'http://127.0.0.1:5174',
    'http://localhost:5175',
    'http://127.0.0.1:5175',
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5174',
    'http://127.0.0.1:5174',
    'http://localhost:5175',
    'http://127.0.0.1:5175',
]

CORS_ALLOW_HEADERS = list(default_headers)

# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------

INSTALLED_APPS = [

    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Apps
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',

    # Shared Masters Apps
    'common_master',
    'login_home',

    # Local Task Management Apps
    'tasks',
    'followups',
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --------------------------------------------------
# ROOT URL CONFIG
# --------------------------------------------------

ROOT_URLCONF = 'TASK_MANAGEMENT.urls'

WSGI_APPLICATION = 'TASK_MANAGEMENT.wsgi.application'

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DATABASES = {

    # DEFAULT DATABASE
    'default': {
        'ENGINE': 'django.db.backends.mysql',

        'NAME': 'task_management_db',

        'USER': 'root',

        'PASSWORD': 'admin@123',

        'HOST': '127.0.0.1',

        'PORT': '3306',

        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",

            'charset': 'utf8mb4',
        },
    },

    # TASK MANAGEMENT DATABASE
    'task_management_db': {
        'ENGINE': 'django.db.backends.mysql',

        'NAME': 'task_management_db',

        'USER': 'root',

        'PASSWORD': 'admin@123',

        'HOST': '127.0.0.1',

        'PORT': '3306',

        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",

            'charset': 'utf8mb4',
        },
    },

    # MASTERS DATABASE
    'masters_db': {
        'ENGINE': 'django.db.backends.mysql',

        'NAME': 'masters_db',

        'USER': 'root',

        'PASSWORD': 'admin@123',

        'HOST': '127.0.0.1',

        'PORT': '3306',

        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",

            'charset': 'utf8mb4',

            'use_unicode': True,
        },
    },
}

# --------------------------------------------------
# DATABASE ROUTERS
# --------------------------------------------------

DATABASE_ROUTERS = [
    'TASK_MANAGEMENT.dbroutes.AuthRouter',
]

# --------------------------------------------------
# DJANGO REST FRAMEWORK
# --------------------------------------------------

REST_FRAMEWORK = {

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_AUTHENTICATION_CLASSES': [

        'rest_framework.authentication.TokenAuthentication',

        'rest_framework.authentication.SessionAuthentication',
    ],
}

# --------------------------------------------------
# SWAGGER SETTINGS
# --------------------------------------------------

SPECTACULAR_SETTINGS = {

    'TITLE': 'Task Management API',

    'VERSION': '1.0.0',
}

# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

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

# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

STATIC_URL = 'static/'

# --------------------------------------------------
# DEFAULT PRIMARY KEY
# --------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'