"""
tasks_app.api.urls
======================

URL routes for the tasks_app API endpoints.
"""

# Third-party
from django.urls import path

# Local
from .views import TaskCreateView, TaskDetailView

urlpatterns = [
    path("tasks/", TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),
]
