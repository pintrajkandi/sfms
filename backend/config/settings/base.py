"""
Base settings shared across environments.

Multi-tenancy: django-tenants (PostgreSQL schema per tenant).
Config is 12-factor — everything comes from environment variables.
"""

from pathlib import Path

import environ

from config.logging import build_logging_config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["*"]),
)

# Read .env if present (docker-compose injects real env vars in prod).
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# --------------------------------------------------------------------------- #
# Applications — SHARED_APPS live in the public schema, TENANT_APPS per school.
# --------------------------------------------------------------------------- #
SHARED_APPS = [
    "django_tenants",  # must be first
    "apps.tenants",  # Client / Domain registry (public only)
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "apps.accounts",  # custom user model
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "apps.accounts",
    "apps.core",
    "apps.schools",
    "apps.students",
    "apps.fees",
    "apps.collections",
    "apps.staff",
    "apps.expenses",
    "apps.inventory",
    "apps.finance",
    "apps.transport",
    "apps.notifications",
    "apps.portal",
    "apps.privacy",
]

INSTALLED_APPS = list(SHARED_APPS) + [a for a in TENANT_APPS if a not in SHARED_APPS]

TENANT_MODEL = "tenants.Client"
TENANT_DOMAIN_MODEL = "tenants.Domain"

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    # WhiteNoise serves /static/ (incl. admin assets) and short-circuits before the
    # tenant middleware, so static requests never need a resolved schema.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Gate the platform admin path by IP (no-op unless ADMIN_IP_ALLOWLIST is set).
    "apps.core.middleware.AdminIPAllowlistMiddleware",
    "django_tenants.middleware.main.TenantMainMiddleware",  # first for all app requests
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Idle-timeout the admin console (needs request.user; admin-path only).
    "apps.core.middleware.AdminSessionTimeoutMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestContextMiddleware",  # attaches tenant/user to logs
]

ROOT_URLCONF = "config.urls"  # tenant-scoped routes
PUBLIC_SCHEMA_URLCONF = "config.urls_public"  # public schema routes (provisioning/admin)

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
ASGI_APPLICATION = "config.asgi.application"

# --------------------------------------------------------------------------- #
# Database — tenant-aware PostgreSQL backend + tenant router.
# --------------------------------------------------------------------------- #
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": env("POSTGRES_DB", default="sfms"),
        "USER": env("POSTGRES_USER", default="sfms"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="sfms"),
        "HOST": env("POSTGRES_HOST", default="postgres"),
        "PORT": env.int("POSTGRES_PORT", default=5432),
    }
}
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- #
# Cache / sessions — Redis, tenant-scoped keys enforced in apps.core.cache.
# --------------------------------------------------------------------------- #
REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_FUNCTION": "apps.core.cache.tenant_key_func",
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# --------------------------------------------------------------------------- #
# Celery + RabbitMQ (broker) / Redis (result backend).
# --------------------------------------------------------------------------- #
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="amqp://guest:guest@rabbitmq:5672//")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TRACK_STARTED = True

# --------------------------------------------------------------------------- #
# Object storage — MinIO (S3-compatible) via django-storages.
# --------------------------------------------------------------------------- #
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": env("MINIO_ACCESS_KEY", default="minioadmin"),
            "secret_key": env("MINIO_SECRET_KEY", default="minioadmin"),
            "bucket_name": env("MINIO_BUCKET", default="sfms-media"),
            "endpoint_url": env("MINIO_ENDPOINT", default="http://minio:9000"),
            "region_name": env("MINIO_REGION", default="us-east-1"),
            "addressing_style": "path",
            # Server talks to minio:9000; browsers get a public host they can reach.
            # (Bucket is anonymous-read, so unsigned URLs are fine.)
            "custom_domain": env("MINIO_PUBLIC_DOMAIN", default="localhost:9000/sfms-media"),
            "url_protocol": "http:",
            "querystring_auth": False,
            "file_overwrite": False,
        },
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --------------------------------------------------------------------------- #
# DRF
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        # Per-action RBAC — only bites viewsets that declare `rbac_resource`.
        "apps.accounts.permissions.RolePermission",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# --------------------------------------------------------------------------- #
# Passwords / i18n
# --------------------------------------------------------------------------- #
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
# CORS (frontend dev server).
# --------------------------------------------------------------------------- #
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://.*\.localhost:\d+$", r"^http://localhost:\d+$"]
CORS_ALLOW_CREDENTIALS = True

# --------------------------------------------------------------------------- #
# Logging — three levels only: info / warn / error (see config/logging.py & §9).
# --------------------------------------------------------------------------- #
LOGGING = build_logging_config(level=env("LOG_LEVEL", default="INFO"))

# --------------------------------------------------------------------------- #
# Money defaults.
# --------------------------------------------------------------------------- #
DEFAULT_CURRENCY = env("DEFAULT_CURRENCY", default="INR")

# --------------------------------------------------------------------------- #
# Platform admin console (public schema, superuser-only). The path is
# env-driven so the master console isn't at the well-known /admin/; an optional
# IP allowlist (comma-separated) restricts who can even reach it.
# --------------------------------------------------------------------------- #
ADMIN_URL = env("ADMIN_URL", default="admin/")
ADMIN_IP_ALLOWLIST = env.list("ADMIN_IP_ALLOWLIST", default=[])
# Idle timeout for the admin console (seconds) — logs an operator out after
# inactivity, independent of the SPA's session. Sensitive actions (provision /
# suspend) additionally require authentication within ADMIN_REAUTH_WINDOW.
ADMIN_SESSION_TIMEOUT = env.int("ADMIN_SESSION_TIMEOUT", default=1800)  # 30 min
ADMIN_REAUTH_WINDOW = env.int("ADMIN_REAUTH_WINDOW", default=600)  # 10 min

# --------------------------------------------------------------------------- #
# Auth0 (optional SSO for tenant login). When AUTH0_DOMAIN + AUTH0_AUDIENCE are
# set, the /auth/auth0/ endpoint validates Auth0 access tokens and maps the
# identity to a tenant user. Leave blank to keep password-only login.
# --------------------------------------------------------------------------- #
AUTH0_DOMAIN = env("AUTH0_DOMAIN", default="")
AUTH0_AUDIENCE = env("AUTH0_AUDIENCE", default="")
AUTH0_EMAIL_CLAIM = env("AUTH0_EMAIL_CLAIM", default="email")

# --------------------------------------------------------------------------- #
# Razorpay (optional online payment gateway + auto-reconciliation). When
# RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET are set the /payments/razorpay/ endpoints
# and the webhook become active; otherwise they degrade to a 503. Never log the
# secret or webhook secret. See apps.collections.gateway.
# --------------------------------------------------------------------------- #
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET", default="")
# Online payments are available only when both key id and secret are set. Read
# via apps.collections.gateway.razorpay_enabled() (settings only exposes
# UPPERCASE names, so the check lives with the gateway, not here).

# --------------------------------------------------------------------------- #
# WhatsApp (MSG91) — parent receipts / reminders / OTP. Blank = disabled; the
# messaging layer falls back to logging the message (so OTPs are visible in dev).
# Enabled check lives in apps.notifications.messaging.whatsapp_enabled().
# --------------------------------------------------------------------------- #
MSG91_WHATSAPP_AUTHKEY = env("MSG91_WHATSAPP_AUTHKEY", default="")
MSG91_WHATSAPP_NUMBER = env("MSG91_WHATSAPP_NUMBER", default="")  # integrated WA number
MSG91_WHATSAPP_NAMESPACE = env("MSG91_WHATSAPP_NAMESPACE", default="")

# SMS (MSG91). Blank = disabled; the messaging layer logs the message (dev fallback).
# Enabled check lives in apps.notifications.messaging.sms_enabled().
MSG91_SMS_AUTHKEY = env("MSG91_SMS_AUTHKEY", default="")
MSG91_SMS_SENDER_ID = env("MSG91_SMS_SENDER_ID", default="")  # 6-char DLT sender id
MSG91_SMS_TEMPLATE_ID = env("MSG91_SMS_TEMPLATE_ID", default="")  # DLT-approved template
# Prefixed to bare 10-digit phone numbers when building an msisdn for sending.
SMS_DEFAULT_COUNTRY_CODE = env("SMS_DEFAULT_COUNTRY_CODE", default="91")

# --------------------------------------------------------------------------- #
# Staged fee reminders — days BEFORE the due date to nudge (T-N), plus a
# recurring cadence once overdue. Read by apps.notifications.tasks.
# --------------------------------------------------------------------------- #
FEE_REMINDER_DAYS_BEFORE = env.list("FEE_REMINDER_DAYS_BEFORE", cast=int, default=[7, 3, 0])
FEE_REMINDER_OVERDUE_EVERY_DAYS = env.int("FEE_REMINDER_OVERDUE_EVERY_DAYS", default=7)

# --------------------------------------------------------------------------- #
# GST e-invoicing (India, optional). When GST_EINVOICE_BASE_URL + API creds are
# set, e-invoices are registered with the IRP for a real IRN/QR; otherwise the
# service falls back to a deterministic mock IRN/QR (dev). Never log the API
# password. Enabled check lives in apps.collections.gst.einvoice_enabled().
# --------------------------------------------------------------------------- #
GST_EINVOICE_BASE_URL = env("GST_EINVOICE_BASE_URL", default="")
GST_EINVOICE_API_USER = env("GST_EINVOICE_API_USER", default="")
GST_EINVOICE_API_PASSWORD = env("GST_EINVOICE_API_PASSWORD", default="")
GST_EINVOICE_GSTIN = env("GST_EINVOICE_GSTIN", default="")  # supplier GSTIN
GST_SUPPLIER_STATE = env("GST_SUPPLIER_STATE", default="")  # supplier state (place of supply)

# Cheque-bounce handling: default charge levied on a dishonoured cheque.
CHEQUE_BOUNCE_CHARGE = env("CHEQUE_BOUNCE_CHARGE", default="0")

# --------------------------------------------------------------------------- #
# AI collections assistant (optional). When ANTHROPIC_API_KEY is set, the
# /collections/assistant/ endpoint answers natural-language questions over the
# tenant's collection data using Claude; otherwise it returns a deterministic
# rule-based summary. Enabled check lives in apps.collections.assistant.
# --------------------------------------------------------------------------- #
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", default="claude-opus-4-8")

# --------------------------------------------------------------------------- #
# Payroll — statutory deduction defaults (India). Overridable per env; a payout
# may also override any component explicitly. PF: 12% of basic capped at a wage
# ceiling; ESI: 0.75% of gross while gross ≤ threshold; a flat professional tax.
# --------------------------------------------------------------------------- #
PAYROLL_PF_RATE = env("PAYROLL_PF_RATE", default="0.12")
PAYROLL_PF_WAGE_CEILING = env("PAYROLL_PF_WAGE_CEILING", default="15000")
PAYROLL_ESI_EMPLOYEE_RATE = env("PAYROLL_ESI_EMPLOYEE_RATE", default="0.0075")
PAYROLL_ESI_WAGE_THRESHOLD = env("PAYROLL_ESI_WAGE_THRESHOLD", default="21000")
PAYROLL_PROFESSIONAL_TAX = env("PAYROLL_PROFESSIONAL_TAX", default="200")

# --------------------------------------------------------------------------- #
# Parent portal — OTP + short-lived signed access token (no parent User model).
# --------------------------------------------------------------------------- #
PARENT_OTP_TTL = env.int("PARENT_OTP_TTL", default=300)  # seconds
PARENT_TOKEN_TTL = env.int("PARENT_TOKEN_TTL", default=1800)  # seconds

# Base domain schools sign in from: <slug>.<TENANT_BASE_DOMAIN>.
# Dev uses ".localhost" (browsers resolve *.localhost to 127.0.0.1); prod uses feeledger.app.
TENANT_BASE_DOMAIN = env("TENANT_BASE_DOMAIN", default="localhost")

# Frontend origin used to build links inside emails (password reset, etc.).
FRONTEND_SCHEME = env("FRONTEND_SCHEME", default="http")
FRONTEND_PORT = env("FRONTEND_PORT", default="5173")

# --------------------------------------------------------------------------- #
# Email — MSG91 SMTP relay. Falls back to the console backend when no SMTP user
# is configured (dev), so password-reset works out of the box without creds.
# --------------------------------------------------------------------------- #
EMAIL_HOST = env("EMAIL_HOST", default="smtp.msg91.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=15)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Fee Ledger <no-reply@feeledger.app>")
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.smtp.EmailBackend"
        if EMAIL_HOST_USER
        else "django.core.mail.backends.console.EmailBackend"
    ),
)
