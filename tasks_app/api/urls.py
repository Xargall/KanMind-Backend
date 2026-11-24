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
)

urlpatterns = [
    path("tasks/", TaskCreateView.as_view(), name="task-create"),
    path(
        "tasks/assigned-to-me/", TaskAssignedToMeView.as_view(), name="assigned-tasks"
    ),
    path("tasks/reviewing/", TaskReviewingView.as_view(), name="reviewed-tasks"),
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),
]
