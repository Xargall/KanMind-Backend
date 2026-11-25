"""
board_app.admin
==============

Registers the Board model for the Django admin interface.
"""

# Third-party
from django.contrib import admin

# Local
from .models import Board

admin.site.register(Board)
