"""
boards_app.models
===================

Board model: a Kanban board with one owner and multiple members.
"""

# Third party
from django.conf import settings
from django.db import models


class Board(models.Model):
    """A Kanban board owned by one user and shared with member users."""

    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_boards"
    )
    member = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="boards", blank=True
    )

    def __str__(self):
        return self.title
