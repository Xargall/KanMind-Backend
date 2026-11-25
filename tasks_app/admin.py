"""
tasks_app.admin
==============

Registers the cTask and Comment model for the Django admin interface.
"""

# Third-party
from django.contrib import admin

# Local
from .models import Task, Comment

admin.site.register(Task)
admin.site.register(Comment)
