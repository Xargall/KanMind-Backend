"""
tasks_app.api.views
============================

Views for the task endpoints.
"""

from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, status, mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Task, Comment
from .permissions import (
    IsTaskBoardMember,
    IsTaskCreatorOrBoardOwner,
    IsCommentCreator,
    IsTaskBoardMemberForComments,
)
from .serializers import (
    TaskCreateSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
    CommentSerializer,
)
from boards_app.models import Board


class TaskCreateView(generics.CreateAPIView):
    """Creates a task on a board; only board owner/members may do so (POST /api/tasks/)."""

    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Checks board membership manually (no permission class), then returns the full TaskSerializer representation."""
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
        task = serializer.save(created_by=request.user)

        output_serializer = TaskSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class TaskDetailView(mixins.DestroyModelMixin, generics.UpdateAPIView):
    """Updates a task; only board owner/members may edit it (PATCH /api/tasks/{task_id}/)."""

    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    lookup_url_kwarg = "task_id"

    def get_permissions(self):
        """Uses the stricter creator-or-owner permission for DELETE, the member permission otherwise."""

        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        return [IsAuthenticated(), IsTaskBoardMember()]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TaskSerializer(instance).data)

    def delete(self, request, *args, **kwargs):
        """Delegates to DestroyModelMixin.destroy(), which applies the DELETE permission above."""
        return self.destroy(request, *args, **kwargs)


class TaskAssignedToMeView(generics.ListAPIView):
    """Lists tasks assigned to or reviewed by the current user (GET /api/tasks/assigned-to-me/)."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            Q(assignee=self.request.user) | Q(reviewer=self.request.user)
        )


class TaskReviewingView(generics.ListAPIView):
    """Lists tasks where the current user is reviewer (GET /api/tasks/reviewing/)."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    """Lists and creates comments on a task; only board members may access (GET/POST /api/tasks/{task_id}/comments/)."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardMemberForComments]

    def get_queryset(self):
        return Comment.objects.filter(task_id=self.kwargs["task_id"])

    def perform_create(self, serializer):
        """Sets task and author server-side; the client cannot set either."""
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        serializer.save(task=task, author=self.request.user)


class CommentDeleteView(generics.DestroyAPIView):
    """Deletes a comment; only its author may do so (DELETE /api/tasks/{task_id}/comments/{comment_id}/)."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentCreator]
    lookup_url_kwarg = "comment_id"

    def get_queryset(self):
        """Scoped by task_id too, so a comment_id from another task correctly returns 404."""
        return Comment.objects.filter(task_id=self.kwargs["task_id"])
