"""
auth_app.api.views
===================

Views for the registration endpoint.
"""

from rest_framework import generics, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import get_user_model

from .serializers import RegistrationSerializer, LoginSerializer, PublicUserSerializer

User = get_user_model()


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


class EmailCheckView(generics.GenericAPIView):
    """Checks whether a user with the given email exists."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublicUserSerializer

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"detail": "Email query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"detail": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No user found with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
