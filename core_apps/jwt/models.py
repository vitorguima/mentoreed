from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from rest_framework.authtoken.models import Token as DefaultTokenModel


def get_token_model():
    token_model = import_string(settings.TOKEN_MODEL)
    session_login = settings.SESSION_LOGIN
    use_jwt = settings.USE_JWT

    if not any((session_login, token_model, use_jwt)):
        raise ImproperlyConfigured(
            "No authentication is configured for rest auth. You must enable one or "
            "more of `TOKEN_MODEL`, `USE_JWT` or `SESSION_LOGIN`"
        )
    if (
        token_model == DefaultTokenModel
        and "rest_framework.authtoken" not in settings.INSTALLED_APPS
    ):
        raise ImproperlyConfigured(
            "You must include `rest_framework.authtoken` in INSTALLED_APPS "
            "or set TOKEN_MODEL to None"
        )
    return token_model


TokenModel = get_token_model()
