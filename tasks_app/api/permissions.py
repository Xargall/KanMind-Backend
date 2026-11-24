"""
tasks_app.api.permissions
============================

Permission classes for the task endpoints.
"""

# Third party
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

# Local
from ..models import Task


class IsTaskBoardMember(BasePermission):
    """Allows access only to users who are owner or member of the task's board."""

    message = "You must be a member of the board this task belongs to."

    def has_object_permission(self, request, view, obj):
        board = obj.board
        return (
            request.user == board.owner
            or board.members.filter(id=request.user.id).exists()
        )


class IsTaskCreatorOrBoardOwner(BasePermission):
    """Allows delete of task only for task creator or board owner."""

    message = "Only the creator of the task or the board owner can delete it."

    def has_object_permission(self, request, view, obj):
        return request.user == obj.created_by or request.user == obj.board.owner


class IsTaskBoardMemberForComments(BasePermission):
    """Allows access only to board members of the task referenced in the URL."""

    message = "You must be a member of the board this task belongs to."

    def has_permission(self, request, view):
        task = get_object_or_404(Task, pk=view.kwargs["task_id"])
        return (
            request.user == task.board.owner
            or task.board.members.filter(id=request.user.id).exists()
        )


class IsCommentCreator(BasePermission):
    """Allows comment delete only by the author."""

    message = "Only the author of the comment can delete it."

    def has_object_permission(self, request, view, obj):
        return request.user == obj.author
