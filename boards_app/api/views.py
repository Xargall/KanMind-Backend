"""
boards_app.api.views
======================

Views for board endpoints.
"""

# Third party
from django.db.models import Q
from rest_framework import generics, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Local
from ..models import Board
from .serializers import (
    BoardListSerializer,
    BoardCreateSerializer,
    BoardDetailSerializer,
    BoardUpdateSerializer
)
from .permissions import IsBoardMemberOrOwner


class BoardListCreateView(generics.ListCreateAPIView):
    """Handles GET /api/boards/ (list) and POST /api/boards/ (create)."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BoardCreateSerializer
        return BoardListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save()

        output_serializer = BoardListSerializer(board)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class BoardDetailView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView,
):
    """Handles GET (detail) and PATCH (update title/members) for /api/boards/{board_id}/."""

    queryset = Board.objects.all()
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner]
    lookup_url_kwarg = "board_id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
