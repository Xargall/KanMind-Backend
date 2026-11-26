"""
tasks_app.api.urls
======================

URL routes for the tasks_app API endpoints.
"""

# Third-party
from django.urls import path

# Local
from .views import (
    TaskCreateView,
    TaskDetailView,
    TaskAssignedToMeView,
    TaskReviewingView,
    CommentListCreateView,
    CommentDeleteView,
)

urlpatterns = [
    path("tasks/", TaskCreateView.as_view(), name="task-create"),
    path(
        "tasks/assigned-to-me/", TaskAssignedToMeView.as_view(), name="assigned-tasks"
    ),
    path("tasks/reviewing/", TaskReviewingView.as_view(), name="reviewed-tasks"),
    path(
        "tasks/<int:task_id>/comments/",
        CommentListCreateView.as_view(),
        name="tasks-comments",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        CommentDeleteView.as_view(),
        name="comment-delete",
    ),
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),
]
