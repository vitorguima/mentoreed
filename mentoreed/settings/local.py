from .base import *  # noqa
from .base import env

# SECURITY WARNING: keep the secret key used in production secret!
# generated using python -c "import secrets; print(secrets.token_urlsafe(38))"
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="JkNRnzZ8z1yBCw8jFkBpQNHDo0v9qDeZAaouOvL2uV2AuWm8y8A",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

CSRF_TRUSTED_ORIGINS = ["http://localhost:8080"]

EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="mailhog")
EMAIL_PORT = env("EMAIL_PORT")
DEFAULT_FROM_EMAIL = "email@email.com"
DOMAIN = env("DOMAIN")
SITE_NAME = "Mentoreed"
