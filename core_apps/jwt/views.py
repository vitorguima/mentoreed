from allauth.account import app_settings as allauth_account_settings
from allauth.account.utils import complete_signup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import TokenModel
from .utils import jwt_encode

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        "password",
        "old_password",
        "new_password1",
        "new_password2",
    ),
)

RegisterSerializer = import_string(settings.REGISTER_SERIALIZER)
register_permission_classes = tuple(
    import_string(c) for c in settings.REGISTER_PERMISSION_CLASSES
)
JWTSerializer = import_string(settings.JWT_SERIALIZER)


class RegisterView(CreateAPIView):
    """
    Registers a new user.

    Accepts the following POST parameters: username, email, password1, password2.
    """

    serializer_class = RegisterSerializer
    permission_classes = register_permission_classes
    authentication_classes = ()
    token_model = TokenModel
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_response_data(self, user):
        if (
            allauth_account_settings.EMAIL_VERIFICATION
            == allauth_account_settings.EmailVerificationMethod.MANDATORY
        ):
            return {"detail": _("Verification e-mail sent.")}

        if settings.USE_JWT:
            data = {
                "user": user,
                "access": self.access_token,
                "refresh": self.refresh_token,
            }
            return JWTSerializer(data, context=self.get_serializer_context()).data
        # elif self.token_model:
        #     return settings.TOKEN_SERIALIZER(
        #         user.auth_token, context=self.get_serializer_context()
        #     ).data
        return None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = self.get_response_data(user)

        if data:
            response = Response(
                data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        else:
            response = Response(status=status.HTTP_204_NO_CONTENT, headers=headers)

        return response

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        if (
            allauth_account_settings.EMAIL_VERIFICATION
            != allauth_account_settings.EmailVerificationMethod.MANDATORY
        ):
            if settings.USE_JWT:
                self.access_token, self.refresh_token = jwt_encode(user)
            elif self.token_model:
                settings.TOKEN_CREATOR(self.token_model, user, serializer)

        complete_signup(
            self.request._request,
            user,
            allauth_account_settings.EMAIL_VERIFICATION,
            None,
        )
        return user


class LoginView(GenericAPIView):
    """
    Check the credentials and return the REST Token
    if the credentials are valid and authenticated.
    Calls Django Auth login method to register User ID
    in Django session framework

    Accept the following POST parameters: username, password
    Return the REST Framework Token Object's key.
    """

    permission_classes = (AllowAny,)
    # TO DO: Add login serializer
    serializer_class = settings.LOGIN_SERIALIZER
    # TO DO: add specific throttle class for login
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    user = None
    access_token = None
    token = None

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def process_login(self):
        django_login(self.request, self.user)

    def get_response_serializer(self):
        if settings.USE_JWT:
            if settings.JWT_AUTH_RETURN_EXPIRATION:
                response_serializer = settings.JWT_SERIALIZER_WITH_EXPIRATION
            else:
                response_serializer = settings.JWT_SERIALIZER

        # else:
        #     response_serializer = settings.TOKEN_SERIALIZER
        return response_serializer

    def login(self):
        self.user = self.serializer.validated_data["user"]

        if settings.USE_JWT:
            self.access_token, self.refresh_token = jwt_encode(self.user)

        # if settings.SESSION_LOGIN:
        #     self.process_login()

    def get_response(self):
        serializer_class = self.get_response_serializer()

        if settings.USE_JWT:
            from rest_framework_simplejwt.settings import (
                settings as jwt_settings,
            )

            access_token_expiration = (
                timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME
            )
            refresh_token_expiration = (
                timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME
            )
            return_expiration_times = jwt_settings.JWT_AUTH_RETURN_EXPIRATION
            auth_httponly = jwt_settings.JWT_AUTH_HTTPONLY

            data = {
                "user": self.user,
                "access": self.access_token,
            }

            if not auth_httponly:
                data["refresh"] = self.refresh_token
            else:
                # Wasnt sure if the serializer needed this
                data["refresh"] = ""

            if return_expiration_times:
                data["access_expiration"] = access_token_expiration
                data["refresh_expiration"] = refresh_token_expiration

            serializer = serializer_class(
                instance=data,
                context=self.get_serializer_context(),
            )
        elif self.token:
            serializer = serializer_class(
                instance=self.token,
                context=self.get_serializer_context(),
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

        response = Response(serializer.data, status=status.HTTP_200_OK)
        if settings.USE_JWT:
            from .serializers import set_jwt_cookies

            set_jwt_cookies(response, self.access_token, self.refresh_token)
        return response

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()


class LogoutView(APIView):
    """
    Calls Django logout method and delete the Token object
    assigned to the current User object.

    Accepts/Returns nothing.
    """

    permission_classes = (AllowAny,)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def get(self, request, *args, **kwargs):
        if getattr(settings, "ACCOUNT_LOGOUT_ON_GET", False):
            response = self.logout(request)
        else:
            response = self.http_method_not_allowed(request, *args, **kwargs)

        return self.finalize_response(request, response, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.logout(request)

    def logout(self, request):
        if not (request.auth or settings.USE_JWT or settings.SESSION_LOGIN):
            return Response(
                {
                    "detail": _(
                        "You should be logged in to logout. Check whether the token is passed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            request.user.auth_token.delete()
        except (AttributeError, ObjectDoesNotExist):
            pass

        if settings.SESSION_LOGIN:
            django_logout(request)

        response = Response(
            {"detail": _("Successfully logged out.")},
            status=status.HTTP_200_OK,
        )

        if settings.USE_JWT:
            # NOTE: this import occurs here rather than at the top level
            # because JWT support is optional, and if `USE_JWT` isn't
            # True we shouldn't need the dependency
            from rest_framework_simplejwt.exceptions import TokenError
            from rest_framework_simplejwt.tokens import RefreshToken

            from .serializers import unset_jwt_cookies

            cookie_name = settings.JWT_AUTH_COOKIE

            unset_jwt_cookies(response)

            if "rest_framework_simplejwt.token_blacklist" in settings.INSTALLED_APPS:
                # add refresh token to blacklist
                try:
                    token: RefreshToken = RefreshToken(None)
                    if settings.JWT_AUTH_HTTPONLY:
                        try:
                            token = RefreshToken(
                                request.COOKIES[settings.JWT_AUTH_REFRESH_COOKIE]
                            )
                        except KeyError:
                            response.data = {
                                "detail": _(
                                    "Refresh token was not included in cookie data."
                                )
                            }
                            response.status_code = status.HTTP_401_UNAUTHORIZED
                    else:
                        try:
                            token = RefreshToken(request.data["refresh"])
                        except KeyError:
                            response.data = {
                                "detail": _(
                                    "Refresh token was not included in request data."
                                )
                            }
                            response.status_code = status.HTTP_401_UNAUTHORIZED

                    token.blacklist()
                except (TokenError, AttributeError, TypeError) as error:
                    if hasattr(error, "args"):
                        if (
                            "Token is blacklisted" in error.args
                            or "Token is invalid or expired" in error.args
                        ):
                            response.data = {"detail": _(error.args[0])}
                            response.status_code = status.HTTP_401_UNAUTHORIZED
                        else:
                            response.data = {"detail": _("An error has occurred.")}
                            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

                    else:
                        response.data = {"detail": _("An error has occurred.")}
                        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            elif not cookie_name:
                message = _(
                    "Neither cookies or blacklist are enabled, so the token "
                    "has not been deleted server side. Please make sure the token is deleted client side.",
                )
                response.data = {"detail": message}
                response.status_code = status.HTTP_200_OK
        return response


class UserDetailsView(RetrieveUpdateAPIView):
    """
    Reads and updates UserModel fields
    Accepts GET, PUT, PATCH methods.

    Default accepted fields: username, first_name, last_name
    Default display fields: pk, username, email, first_name, last_name
    Read-only fields: pk, email

    Returns UserModel fields.
    """

    serializer_class = settings.USER_DETAILS_SERIALIZER
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        """
        Adding this method since it is sometimes called when using
        django-rest-swagger
        """
        return get_user_model().objects.none()
