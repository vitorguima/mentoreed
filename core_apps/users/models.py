from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    This allows for additional fields and methods in the future.
    """

    # Add any additional fields or methods here if needed
    pass
