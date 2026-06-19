"""
Production settings — import from base settings and override.

Usage:
  Set environment variable: DJANGO_SETTINGS_MODULE=config.settings_production
  Or in manage.py: os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
"""
from .settings import *
from decouple import config

# Security
DEBUG        = False
SECRET_KEY   = config("SECRET_KEY")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="").split(",")

# Database (same as dev but from env)
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     config("DB_NAME"),
        "USER":     config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST":     config("DB_HOST", default="localhost"),
        "PORT":     config("DB_PORT", default="5432"),
    }
}

# Security headers
SECURE_BROWSER_XSS_FILTER       = True
SECURE_CONTENT_TYPE_NOSNIFF     = True
X_FRAME_OPTIONS                 = "DENY"
SECURE_SSL_REDIRECT             = True
SESSION_COOKIE_SECURE           = True
CSRF_COOKIE_SECURE              = True
SECURE_HSTS_SECONDS             = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS  = True

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT  = BASE_DIR / "media"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{"
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs/errors.log",
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "WARNING",
    },
}
