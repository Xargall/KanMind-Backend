"""
board_app.admin
==============

Registers the Board model for the Django admin interface.
"""

from django.contrib import admin

from .models import Board

admin.site.register(Board)
