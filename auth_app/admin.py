"""
auth_app.admin
==============

Registers the custom User model for the Django admin interface.
"""

# Third-party
from django.contrib import admin

# Local
from .models import User

admin.site.register(User)
