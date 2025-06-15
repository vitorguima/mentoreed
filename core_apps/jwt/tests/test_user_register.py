import pytest
from allauth.socialaccount.models import EmailAddress
from django.contrib.auth import get_user_model

from core_apps.jwt.tests.factories import EmailAddressFactory
from core_apps.users.tests.factories import UserFactory

from django.test import override_settings

User = get_user_model()


@pytest.mark.django_db
@override_settings(ACCOUNT_UNIQUE_EMAIL=True)
def test_user_can_register(client):
    """ "
    Test that a user can register with valid data.
    """

    username = "testuser"
    email = "test@gmail.com"
    password = "testpassword"

    response = client.post(
        "/api/v1/auth/register",
        {
            "username": username,
            "email": email,
            "password1": "testpassword",
            "password2": password,
        },
    )

    content = response.json()

    assert response.status_code == 201
    assert content["user"]["username"] == username
    assert content["user"]["email"] == email
    assert User.objects.filter(username=username, email=email).exists()
    assert EmailAddress.objects.filter(
        user__username=username, email=email, verified=False
    ).exists()


@pytest.mark.django_db
def test_user_registration_with_existing_username(client):
    """
    Test that a user cannot register with an existing username.
    """

    username = "testuser"
    email = "test@gmail.com"
    UserFactory.create(username=username, email=email)
    response = client.post(
        "/api/v1/auth/register",
        {
            "username": username,
            "email": email,
        },
    )

    content = response.json()
    assert response.status_code == 400
    assert content["username"] == ["A user with that username already exists."]


@pytest.mark.django_db
def test_user_registration_with_existing_email(client):
    """
    Test that a user cannot register with an existing email.
    """

    username = "testuser"
    email = "existing@gmail.com"
    user = UserFactory.create(username=username, email=email)
    # EmailAdress instance is created automatically when user is created.
    # TO DO: email verification needs to be implemented yet
    EmailAddressFactory.create(user=user, verified=True, email=email)
    response = client.post(
        "/api/v1/auth/register",
        {
            "username": "newuser",
            "email": email,
            "password1": "testpassword",
            "password2": "testpassword",
        },
    )
    content = response.json()
    assert response.status_code == 400
    assert content["email"] == [
        "A user is already registered with this e-mail address."
    ]


@pytest.mark.django_db
def test_user_registration_with_invalid_email(client):
    """
    Test that a user cannot register with an invalid email.
    """

    response = client.post(
        "/api/v1/auth/register",
        {
            "username": "testuser",
            "email": "invalid-email",
            "password1": "testpassword",
            "password2": "testpassword",
        },
    )

    content = response.json()
    assert response.status_code == 400
    assert content["email"] == ["Enter a valid email address."]


@pytest.mark.django_db
def test_user_registration_with_mismatched_passwords(client):
    """
    Test that a user cannot register with mismatched passwords.
    """

    response = client.post(
        "/api/v1/auth/register",
        {
            "username": "testuser",
            "email": "mismatch@gmail.com",
            "password1": "testpassword",
            "password2": "differentpassword",
        },
    )
    content = response.json()
    assert response.status_code == 400
    assert content["non_field_errors"] == ["The two password fields didn't match."]
