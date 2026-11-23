"""
tasks_app.api.views
============================

Views for the task endpoints.
"""

# Third party
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Local
from ..models import Task
from .permissions import IsTaskBoardMember
from .serializers import TaskCreateSerializer, TaskSerializer, TaskUpdateSerializer
from boards_app.models import Board


class TaskCreateView(generics.CreateAPIView):
    """Creates a task on a board; only board owner/members may do so (POST /api/tasks/)."""

    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        board = get_object_or_404(Board, pk=request.data.get("board"))

        is_member = (
            request.user == board.owner
            or board.members.filter(id=request.user.id).exists()
        )
        if not is_member:
            raise PermissionDenied(
                "You must be a member of the board to create a task."
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        output_serializer = TaskSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class TaskDetailView(generics.UpdateAPIView):
    """Updates a task; only board owner/members may edit it (PATCH /api/tasks/{task_id}/)."""

    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardMember]
    lookup_url_kwarg = "task_id"

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TaskSerializer(instance).data)
