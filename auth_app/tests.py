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
