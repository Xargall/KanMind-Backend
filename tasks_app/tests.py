"""
tasks_app.tests
===================

Tests for the task create/update endpoints.
"""

# Third-party
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Local
from .models import Task
from boards_app.models import Board

User = get_user_model()


class TaskCreateTests(APITestCase):
    """Tests for POST /api/tasks/."""

    def setUp(self):
        self.url = reverse("task-create")

        self.owner = User.objects.create_user(
            email="owner@example.com", password="pass123", fullname="Owner"
        )
        self.member = User.objects.create_user(
            email="member@example.com", password="pass123", fullname="Member"
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com", password="pass123", fullname="Outsider"
        )

        self.board = Board.objects.create(title="Task Board", owner=self.owner)
        self.board.members.add(self.member)

    def test_create_requires_authentication(self):
        """Anonymous requests are rejected."""
        response = self.client.post(
            self.url, {"board": self.board.id, "title": "X"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_create_task(self):
        """A board member can create a task on that board."""
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self.url,
            {
                "board": self.board.id,
                "title": "New Task",
                "description": "Do the thing",
                "status": "to-do",
                "priority": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["board"], self.board.id)
        self.assertIsNone(response.data["assignee"])
        self.assertIsNone(response.data["reviewer"])

    def test_owner_can_create_task(self):
        """The board owner (not necessarily a listed member) can also create a task."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.url, {"board": self.board.id, "title": "Owner Task"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_gets_403(self):
        """A user with no relation to the board cannot create a task on it."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(
            self.url, {"board": self.board.id, "title": "Hacked Task"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_board_gets_404(self):
        """A board ID that doesn't exist at all returns 404, not 403."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.url, {"board": 999999, "title": "Orphan Task"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_assignee_not_board_member_returns_400(self):
        """Assigning a user who isn't a board member is rejected."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.url,
            {
                "board": self.board.id,
                "title": "Bad Assignee",
                "assignee_id": self.outsider.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assignee_and_reviewer_are_nested_in_response(self):
        """A valid assignee/reviewer come back as nested objects, not raw IDs."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.url,
            {
                "board": self.board.id,
                "title": "Assigned Task",
                "assignee_id": self.member.id,
                "reviewer_id": self.owner.id,
            },
            format="json",
        )

        print(response.data)  # <- temporär

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TaskUpdateTests(APITestCase):
    """Tests for PATCH /api/tasks/{task_id}/."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner2@example.com", password="pass123", fullname="Owner2"
        )
        self.member = User.objects.create_user(
            email="member2@example.com", password="pass123", fullname="Member2"
        )
        self.outsider = User.objects.create_user(
            email="outsider2@example.com", password="pass123", fullname="Outsider2"
        )

        self.board = Board.objects.create(title="Update Board", owner=self.owner)
        self.board.members.add(self.member)

        self.task = Task.objects.create(
            board=self.board, title="Original Title", status="to-do", priority="low"
        )

        self.url = reverse("task-detail", kwargs={"task_id": self.task.id})

    def test_member_can_update_task(self):
        """A board member can update a task on that board."""
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(self.url, {"status": "done"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "done")

    def test_owner_can_update_task(self):
        """The board owner can also update a task."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.url, {"priority": "high"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["priority"], "high")

    def test_outsider_gets_403(self):
        """A user with no relation to the board cannot update its tasks."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.patch(self.url, {"title": "Hacked"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_task_gets_404(self):
        """A task ID that doesn't exist returns 404, not 403."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("task-detail", kwargs={"task_id": 999999})
        response = self.client.patch(url, {"title": "Ghost"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_gets_401(self):
        """Anonymous requests are rejected before the permission check even runs."""
        response = self.client.patch(self.url, {"title": "Anon"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_leaves_other_fields_untouched(self):
        """Sending only one field leaves the rest of the task unchanged."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.url, {"status": "review"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Original Title")
        self.assertEqual(response.data["priority"], "low")

    def test_board_field_cannot_be_changed(self):
        """Including `board` in the request has no effect; the task stays on its original board."""
        other_board = Board.objects.create(title="Other Board", owner=self.owner)
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.url, {"board": other_board.id, "title": "Still Here"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.board_id, self.board.id)

    def test_assignee_not_board_member_returns_400(self):
        """Assigning a user who isn't a member of the task's board is rejected."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.url, {"assignee_id": self.outsider.id}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
