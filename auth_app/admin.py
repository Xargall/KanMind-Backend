"""
auth_app.admin
==============

Registers the custom User model for the Django admin interface.
"""

from django.contrib import admin

from .models import User

admin.site.register(User)
