"""
auth_app.api.views
===================

Views for the registration endpoint.
"""

# Third party
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Local

from .serializers import RegistrationSerializer, LoginSerializer


class RegistrationView(generics.CreateAPIView):
    """Handles POST /api/registration/ — creates a new user and returns an auth token."""

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token, _ = Token.objects.get_or_create(user=user)

        data = {
            "token": token.key,
            "fullname": user.fullname,
            "email": user.email,
            "user_id": user.id,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """Handles POST /api/login/ — authenticates a user and returns an auth token."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)

        data = {
            "token": token.key,
            "fullname": user.fullname,
            "email": user.email,
            "user_id": user.id,
        }
        return Response(data, status=status.HTTP_200_OK)
