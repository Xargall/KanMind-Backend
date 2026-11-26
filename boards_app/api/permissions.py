"""
boards_app.api.permissions
=============================

Permission classes for board endpoints.
"""

from rest_framework.permissions import BasePermission


class IsBoardMemberOrOwner(BasePermission):
    """Allows access only to a board's owner or one of its members."""

    message = "You must be the owner or a member of this Board"

    def has_object_permission(self, request, view, obj):
        return (
            obj.owner == request.user or obj.members.filter(id=request.user.id).exists()
        )


class IsBoardOwner(BasePermission):
    """Allows access only to a board's owner (not members)."""

    message = "You must be the owner of this board to perform this action."

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
