"""
Base settings shared across all environments.
"""
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="unsafe-secret-key-for-dev")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # GeoDjango
    "django.contrib.gis",
    # Third-party
    "rest_framework",
    "rest_framework_gis",
    "corsheaders",
    # Local apps
    "core",
    "layers",
    "analysis",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------- Database (PostGIS) ----------
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgis://geo_user:geo_password@localhost:5434/geo_analysis")
}
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# ---------- Internacionalização ----------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ---------- Static ----------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- DRF ----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# ---------- Authentication Backends ----------
# Apenas usuários com role ADMIN no NestJS conseguem acessar o Django Admin.
# O ModelBackend foi removido intencionalmente para impedir login via senha Django local.
AUTHENTICATION_BACKENDS = [
    "core.backends.NestJsAuthBackend",
]

# URL base do backend NestJS (usado pelo NestJsAuthBackend)
NESTJS_BACKEND_URL = env("NESTJS_BACKEND_URL", default="http://localhost:3000")

# ---------- API Key ----------
GEO_API_KEY = env("GEO_API_KEY", default="dev-api-key-change-in-production")

# ---------- CORS ----------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000"],
)
CORS_ALLOW_ALL_ORIGINS = DEBUG

# ---------- Upload ----------
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024   # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024   # 50 MB
