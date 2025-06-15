from django.contrib.auth import get_user_model
from requests import Response
from rest_framework import mixins, status, viewsets

from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(
    mixins.CreateModelMixin,  # register
    mixins.UpdateModelMixin,  # update
    mixins.DestroyModelMixin,  # delete
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer

    # @TO DO: Break this flow into more complex steps when MFA is implemented
    def register(self, request, *args, **kwargs):
        """
        Register a new user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user).data,
                "message": "User registered successfully.",
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """
        Update user details.
        """
        if not request.user.is_authenticated:
            return Response(
                {"message": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check if the user has permission to update
        if not request.user.has_perm("users.update_user"):
            return Response(
                {"message": "You do not have permission to update this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.update()

        return Response(
            {
                "user": UserSerializer(user).data,
                "message": "User updated successfully.",
            },
            status=status.HTTP_200_OK,
        )
