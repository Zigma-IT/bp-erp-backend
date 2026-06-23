"""
Django settings for PROCUREMENT project.
"""

import sys
from pathlib import Path
from corsheaders.defaults import default_headers

# --------------------------------------------------
# BASE DIRECTORY
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MASTERS_DIR = BASE_DIR.parent / "MASTERS"
PROCUREMENT_APPS_DIR = BASE_DIR / "procurement"

if str(MASTERS_DIR) not in sys.path:
    sys.path.insert(0, str(MASTERS_DIR))

if str(PROCUREMENT_APPS_DIR) not in sys.path:
    sys.path.insert(0, str(PROCUREMENT_APPS_DIR))

# --------------------------------------------------
# SECURITY
# --------------------------------------------------

SECRET_KEY = 'django-insecure-$#su%qe)&g)w)p#b-tyb4jn2uskgpap@teh=t5l7^+msh4h1m7'

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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',

    # Local apps
    'common_master',
    'purchase_master',
    'purchase_entrys',
    'purchase_expense',
    'sales',
    'login_home',
    'approvals',
    'reports',
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
# ROOT CONFIG
# --------------------------------------------------

ROOT_URLCONF = 'PROCUREMENT.urls'

WSGI_APPLICATION = 'PROCUREMENT.wsgi.application'

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

    # REQUIRED DEFAULT DATABASE
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'procurement_db1',
        'USER': 'root',
        'PASSWORD': 'admin@123',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    },

    # OPTIONAL SECOND ALIAS
    'procurement_db1': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'procurement_db1',
        'USER': 'root',
        'PASSWORD': 'admin@123',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    },

    # Historical alias if needed
    'masters_db1': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'masters_db1',
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
    'PROCUREMENT.dbrouters.AuthRouter',
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
# SWAGGER / API DOCS
# --------------------------------------------------

SPECTACULAR_SETTINGS = {
    'TITLE': 'Procurement API',
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
