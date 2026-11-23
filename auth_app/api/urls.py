"""
auth_app.api.urls
===================

URL routes for the auth_app API endpoints.
"""

# Third party
from django.urls import path

# Local
from .views import RegistrationView, LoginView

urlpatterns = [
    path("registration/", RegistrationView.as_view(), name="registration"),
    path("login/", LoginView.as_view(), name="login"),
]
