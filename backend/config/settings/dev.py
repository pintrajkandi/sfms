"""Development settings."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Serve static straight from app/finder dirs — no collectstatic needed in dev.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Browsable API is convenient in dev.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Cross-origin auth for the Vite dev server (SPA on :5173 → API on :8000).
# Wildcards cover per-school subdomains (greenfield-high.localhost:5173).
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://*.localhost:5173",
    "http://localhost:8000",
    "http://*.localhost:8000",
    # Public domain (behind Bunny CDN, which terminates TLS). Needed so the admin
    # login POST passes CSRF even though the origin server itself speaks HTTP.
    "https://yukicares.cloud",
    "https://*.yukicares.cloud",
]
# Extra origins can be added per-deploy without a code change (comma-separated).
CSRF_TRUSTED_ORIGINS += env.list("EXTRA_CSRF_TRUSTED_ORIGINS", default=[])
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Sentry is optional in dev; only initialise if a DSN is provided.
SENTRY_DSN = env("SENTRY_DSN", default="")
