"""
auth_app.models
================

Custom User model for KanMind.

Replaces Django's default User because:
- the API consistently expects/returns a single `fullname` string
  instead of separate first_name/last_name
- `email` (not `username`) is used as the login identifier
"""

# Third-party
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extends AbstractUser with fullname; email replaces username as the login identifier"""

    username = None
    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=255)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["fullname"]

    def __str__(self):
        return self.fullname
