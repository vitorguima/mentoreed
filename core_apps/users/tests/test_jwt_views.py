from core_apps.users.tests.factories import UserFactory
import pytest
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

User = get_user_model()

@pytest.mark.django_db
def test_authenticate_with_valid_credentials(client):
    """
    Test that a user can authenticate with valid credentials.
    """

    user = UserFactory.create(username='testuser', password='testpassword')

    response = client.post("/api/v1/auth/login", {
        "username": user.username,
        "password": "testpassword"
    })
    assert response.status_code == 200
    
    content = response.json()

    assert content["access"] is not None
    assert content["refresh"] is not None
    assert content["user"]["username"] == user.username
    assert content["user"]["email"] == user.email
