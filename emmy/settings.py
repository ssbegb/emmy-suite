"""Django settings for Emmy Suite.

Configuration comes from environment variables (see .env.example).
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=""):
    return os.environ.get(name, default)


DEBUG = env("DEBUG", "0") == "1"
SECRET_KEY = env("SECRET_KEY") or ("dev-insecure-key" if DEBUG else "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set when DEBUG is off")
ALLOWED_HOSTS = [h for h in env("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
CSRF_TRUSTED_ORIGINS = [o for o in env("CSRF_TRUSTED_ORIGINS").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    # Emmy core
    "emmy.accounts",
    "emmy.tenancy",
    "emmy.portal",
    "emmy.org",
    # Emmy modules
    "modules.decisions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "emmy.tenancy.middleware.TenantMiddleware",
]

ROOT_URLCONF = "emmy.urls"
WSGI_APPLICATION = "emmy.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "emmy" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "emmy.portal.context_processors.portal",
            ],
        },
    },
]

# --- Database -------------------------------------------------------------
# The web app connects as a limited role (DB_APP_USER) that is subject to
# PostgreSQL row-level security. Schema changes and tests run as the owner
# role (DB_OWNER_USER), which creates the tables and the security policies.
OWNER_COMMANDS = {"migrate", "makemigrations", "sqlmigrate", "showmigrations", "test", "flush"}
USE_OWNER = len(sys.argv) > 1 and sys.argv[1] in OWNER_COMMANDS
DB_APP_USER = env("DB_APP_USER", "emmy_app")

if USE_OWNER:
    _db = {
        "USER": env("DB_OWNER_USER", "emmy"),
        "PASSWORD": env("DB_OWNER_PASSWORD"),
        "HOST": env("DB_OWNER_HOST"),  # empty = local socket (peer auth)
    }
else:
    _db = {
        "USER": DB_APP_USER,
        "PASSWORD": env("DB_APP_PASSWORD"),
        "HOST": env("DB_HOST", "localhost"),
    }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "emmy_suite"),
        "PORT": env("DB_PORT", "5432"),
        **_db,
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TEST_RUNNER = "emmy.test_runner.RLSTestRunner"

# --- Auth -----------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
SITE_ID = 1
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "portal:home"
ACCOUNT_LOGOUT_REDIRECT_URL = "account_login"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", "optional")
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = True
SOCIALACCOUNT_LOGIN_ON_GET = False

SOCIALACCOUNT_PROVIDERS = {}
if env("GOOGLE_CLIENT_ID"):
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APPS": [{"client_id": env("GOOGLE_CLIENT_ID"), "secret": env("GOOGLE_CLIENT_SECRET")}],
        "SCOPE": ["profile", "email"],
    }
if env("MICROSOFT_CLIENT_ID"):
    SOCIALACCOUNT_PROVIDERS["microsoft"] = {
        "APPS": [
            {
                "client_id": env("MICROSOFT_CLIENT_ID"),
                "secret": env("MICROSOFT_CLIENT_SECRET"),
                "settings": {"tenant": "common"},
            }
        ],
    }

# --- Email ----------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Emmy Suite <noreply@localhost>")

# --- i18n / static --------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "emmy" / "static"]

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
