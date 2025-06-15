from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers, status
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import settings as jwt_settings

try:
    from allauth.account import app_settings as allauth_account_settings
    from allauth.account.adapter import get_adapter
    from allauth.account.utils import setup_user_email
    from allauth.socialaccount.models import EmailAddress
    from allauth.utils import get_username_max_length
except ImportError:
    raise ImportError("allauth needs to be added to INSTALLED_APPS.")


UserModel = get_user_model()


def set_jwt_access_cookie(response, access_token):
    cookie_name = settings.JWT_AUTH_COOKIE
    access_token_expiration = timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME
    cookie_secure = settings.JWT_AUTH_SECURE
    cookie_httponly = settings.JWT_AUTH_HTTPONLY
    cookie_samesite = settings.JWT_AUTH_SAMESITE
    cookie_domain = settings.JWT_AUTH_COOKIE_DOMAIN

    if cookie_name:
        response.set_cookie(
            cookie_name,
            access_token,
            expires=access_token_expiration,
            secure=cookie_secure,
            httponly=cookie_httponly,
            samesite=cookie_samesite,
            domain=cookie_domain,
        )


def set_jwt_refresh_cookie(response, refresh_token):
    refresh_token_expiration = timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME
    refresh_cookie_name = settings.JWT_AUTH_REFRESH_COOKIE
    refresh_cookie_path = settings.JWT_AUTH_REFRESH_COOKIE_PATH
    cookie_secure = settings.JWT_AUTH_SECURE
    cookie_httponly = settings.JWT_AUTH_HTTPONLY
    cookie_samesite = settings.JWT_AUTH_SAMESITE
    cookie_domain = settings.JWT_AUTH_COOKIE_DOMAIN

    if refresh_cookie_name:
        response.set_cookie(
            refresh_cookie_name,
            refresh_token,
            expires=refresh_token_expiration,
            secure=cookie_secure,
            httponly=cookie_httponly,
            samesite=cookie_samesite,
            path=refresh_cookie_path,
            domain=cookie_domain,
        )


def set_jwt_cookies(response, access_token, refresh_token):
    set_jwt_access_cookie(response, access_token)
    set_jwt_refresh_cookie(response, refresh_token)


def unset_jwt_cookies(response):
    cookie_name = settings.JWT_AUTH_COOKIE
    refresh_cookie_name = settings.JWT_AUTH_REFRESH_COOKIE
    refresh_cookie_path = settings.JWT_AUTH_REFRESH_COOKIE_PATH
    cookie_samesite = settings.JWT_AUTH_SAMESITE
    cookie_domain = settings.JWT_AUTH_COOKIE_DOMAIN

    if cookie_name:
        response.delete_cookie(
            cookie_name, samesite=cookie_samesite, domain=cookie_domain
        )
    if refresh_cookie_name:
        response.delete_cookie(
            refresh_cookie_name,
            path=refresh_cookie_path,
            samesite=cookie_samesite,
            domain=cookie_domain,
        )


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = serializers.CharField(
        required=False, help_text=_("WIll override cookie.")
    )

    def extract_refresh_token(self):
        request = self.context["request"]
        if "refresh" in request.data and request.data["refresh"] != "":
            return request.data["refresh"]
        cookie_name = settings.JWT_AUTH_REFRESH_COOKIE
        if cookie_name and cookie_name in request.COOKIES:
            return request.COOKIES.get(cookie_name)
        else:
            raise InvalidToken(_("No valid refresh token found."))

    def validate(self, attrs):
        attrs["refresh"] = self.extract_refresh_token()
        return super().validate(attrs)


def get_refresh_view():
    """Returns a Token Refresh CBV without a circular import"""
    from rest_framework_simplejwt.settings import settings as jwt_settings
    from rest_framework_simplejwt.views import TokenRefreshView

    class RefreshViewWithCookieSupport(TokenRefreshView):
        serializer_class = CookieTokenRefreshSerializer

        def finalize_response(self, request, response, *args, **kwargs):
            if response.status_code == status.HTTP_200_OK and "access" in response.data:
                set_jwt_access_cookie(response, response.data["access"])
                response.data["access_expiration"] = (
                    timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME
                )
            if (
                response.status_code == status.HTTP_200_OK
                and "refresh" in response.data
            ):
                set_jwt_refresh_cookie(response, response.data["refresh"])
                if settings.JWT_AUTH_HTTPONLY:
                    del response.data["refresh"]
                else:
                    response.data["refresh_expiration"] = (
                        timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME
                    )
            return super().finalize_response(request, response, *args, **kwargs)

    return RefreshViewWithCookieSupport


class JWTSerializer(serializers.Serializer):
    """
    Serializer for JWT authentication.
    """

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        """
        Required to allow using custom USER_DETAILS_SERIALIZER in
        JWTSerializer. Defining it here to avoid circular imports
        """
        JWTUserDetailsSerializer = import_string(settings.USER_DETAILS_SERIALIZER)

        user_data = JWTUserDetailsSerializer(obj["user"], context=self.context).data
        return user_data


class JWTSerializerWithExpiration(JWTSerializer):
    """
    Serializer for JWT authentication with expiration times.
    """

    access_expiration = serializers.DateTimeField()
    refresh_expiration = serializers.DateTimeField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={"input_type": "password"})

    def authenticate(self, **kwargs):
        return authenticate(self.context["request"], **kwargs)

    def _validate_email(self, email, password):
        if email and password:
            user = self.authenticate(email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username(self, username, password):
        if username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include "username" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username_email(self, username, email, password):
        if email and password:
            user = self.authenticate(email=email, password=password)
        elif username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include either "username" or "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def get_auth_user_using_orm(self, username, email, password):
        if email:
            try:
                username = UserModel.objects.get(email__iexact=email).get_username()
            except UserModel.DoesNotExist:
                pass

        if username:
            return self._validate_username_email(username, "", password)

        return None

    def get_auth_user(self, username, email, password):
        """
        Retrieve the auth user from given POST payload by using
        either `allauth` auth scheme or bare Django auth scheme.

        Returns the authenticated user instance if credentials are correct,
        else `None` will be returned
        """
        return self.get_auth_user_using_orm(username, email, password)

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")
        user = self.get_auth_user(username, email, password)

        if not user:
            msg = _("Unable to log in with provided credentials.")
            raise exceptions.ValidationError(msg)

        # Did we get back an active user?
        self.validate_auth_user_status(user)

        attrs["user"] = user
        return attrs

    @staticmethod
    def validate_auth_user_status(user):
        if not user.is_active:
            msg = _("User account is disabled.")
            raise exceptions.ValidationError(msg)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=get_username_max_length(),
        min_length=allauth_account_settings.USERNAME_MIN_LENGTH,
        required=allauth_account_settings.SIGNUP_FIELDS["username"]["required"],
    )
    email = serializers.EmailField(
        required=allauth_account_settings.SIGNUP_FIELDS["email"]["required"]
    )
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_username(self, username):
        username = get_adapter().clean_username(username)
        return username

    def validate_email(self, email):
        email = get_adapter().clean_email(email)

        if allauth_account_settings.UNIQUE_EMAIL:
            if email and EmailAddress.objects.is_verified(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address."),
                )
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError(
                _("The two password fields didn't match.")
            )
        return data

    def custom_signup(self, request, user):
        pass

    def get_cleaned_data(self):
        return {
            "username": self.validated_data.get("username", ""),
            "password1": self.validated_data.get("password1", ""),
            "email": self.validated_data.get("email", ""),
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        user = adapter.save_user(request, user, self, commit=False)
        if "password1" in self.cleaned_data:
            try:
                adapter.clean_password(self.cleaned_data["password1"], user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    detail=serializers.as_serializer_error(exc)
                )
        user.save()
        self.custom_signup(request, user)
        setup_user_email(request, user, [])
        return user
