"""
tasks_app.api.permissions
============================

Permission classes for the task endpoints.
"""

# Third party
from rest_framework.permissions import BasePermission


class IsTaskBoardMember(BasePermission):
    """Allows access only to users who are owner or member of the task's board."""

    message = "You must be a member of the board this task belongs to."

    def has_object_permission(self, request, view, obj):
        board = obj.board
        return request.user == board.owner or board.members.filter(id=request.user.id).exists()