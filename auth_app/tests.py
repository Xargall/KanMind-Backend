"""
auth_app.tests
================

Tests for the registration endpoint.
"""

# Third-party
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    """Tests for POST /api/registration/."""

    def setUp(self):
        self.url = reverse("registration")
        self.valid_payload = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "repeated_password": "testpassword123",
        }

    def test_registration_success(self):
        """A valid payload creates a user and returns token + user data."""
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["fullname"], self.valid_payload["fullname"])
        self.assertEqual(response.data["email"], self.valid_payload["email"])
        self.assertIn("user_id", response.data)
        self.assertTrue(User.objects.filter(email=self.valid_payload["email"]).exists())

    def test_registration_password_mismatch(self):
        """Mismatched passwords return 400 and create no user."""
        payload = {**self.valid_payload, "repeated_password": "differentpassword"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email=payload["email"]).exists())

    def test_registration_email_already_taken(self):
        """Registering with an already-used email returns 400."""
        User.objects.create_user(
            email=self.valid_payload["email"],
            password="somepassword",
            fullname="Existing User",
        )
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Tests for POST /api/login/."""

    def setUp(self):
        self.url = reverse("login")
        self.password = "testpassword123"
        self.user = User.objects.create_user(
            email="test@example.com",
            password=self.password,
            fullname="Test User",
        )

    def test_login_success(self):
        """Valid credentials return 200 with token and user data."""
        response = self.client.post(
            self.url,
            {"email": self.user.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user_id"], self.user.id)

    def test_login_wrong_password(self):
        """Wrong password returns 400."""
        response = self.client.post(
            self.url,
            {"email": self.user.email, "password": "wrongpassword"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unknown_email(self):
        """Unregistered email returns 400 (not 404 — avoids leaking which emails exist)."""
        response = self.client.post(
            self.url,
            {"email": "unknown@example.com", "password": "irrelevant"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserManagerTests(TestCase):
    """Direct tests for the custom UserManager (not reachable via the public API)."""

    def test_create_superuser_sets_staff_and_superuser_flags(self):
        user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123", fullname="Admin"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_superuser_rejects_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin2@example.com",
                password="pass",
                fullname="Admin2",
                is_staff=False,
            )

    def test_user_str_returns_fullname(self):
        user = User.objects.create_user(
            email="x@example.com", password="pass", fullname="X Y"
        )
        self.assertEqual(str(user), "X Y")
