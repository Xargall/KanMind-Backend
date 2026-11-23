"""
boards_app.api.permissions
=============================

Permission classes for board endpoints.
"""

# Third party
from rest_framework.permissions import BasePermission


class IsBoardMemberOrOwner(BasePermission):
    """Allows access only to a board's owner or one of its members."""

    message = "You must be the owner or a member of this Board"

    def has_object_permission(self, request, view, obj):
        return (
            obj.owner == request.user or obj.members.filter(id=request.user.id).exists()
        )
