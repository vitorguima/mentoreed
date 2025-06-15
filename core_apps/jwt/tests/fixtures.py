import pytest
from rest_framework.test import APIClient as BaseAPIClient

from core_apps.users.tests.factories import UserFactory


class ApiClient(BaseAPIClient):
    """
    Custom API client for testing.
    This can be extended with additional methods or properties as needed.
    """


def client():
    """
    Fixture to provide a basic API client.
    This can be used for tests that do not require authentication.
    """
    return ApiClient()


@pytest.fixture
def authenticated_client(client):
    """
    Fixture to provide an authenticated API client.
    """
    user = UserFactory.create()
    client.force_authenticate(user=user)
    return client
