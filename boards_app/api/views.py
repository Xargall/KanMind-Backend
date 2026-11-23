"""
boards_app.api.views
======================

Views for board endpoints.
"""

# Third party
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

# Local
from ..models import Board
from .serializers import BoardListSerializer


class BoardListView(generics.ListAPIView):
    """Handles GET /api/boards/ — lists boards the user owns or is a member of."""

    serializer_class = BoardListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(member=user)).distinct()
