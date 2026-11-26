"""
auth_app.models
================

Custom User model for KanMind.

Replaces Django's default User because:
- the API consistently expects/returns a single `fullname` string
  instead of separate first_name/last_name
- `email` (not `username`) is used as the login identifier

Includes a custom manager, since Django's built-in UserManager still
expects a `username` argument internally, which no longer exists here.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Creates users by email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Extends AbstractUser with fullname; email replaces username as the login identifier"""

    username = None
    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=255)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["fullname"]

    objects = UserManager()

    def __str__(self):
        return self.fullname
