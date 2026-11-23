"""
boards_app.api.urls
======================

URL routes for the boards_app API endpoints.
"""

# Third-party
from django.urls import path

# Local
from .views import BoardListCreateView

urlpatterns = [
    path("boards/", BoardListCreateView.as_view(), name="board-list-create"),
]
