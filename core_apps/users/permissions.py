from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

User = get_user_model()

class UsersPermissionsBackend(BaseBackend):
    """
    Custom authentication backend to handle user permissions.
    """

    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if the user has a specific permission.
        """
        if not isinstance(user_obj, User):
            return False
        
        if perm == f"{User._meta.app_label}.update_user":
            return user_obj.is_authenticated and user_obj == obj or user_obj.is_superuser
        
