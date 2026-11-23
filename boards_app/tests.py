"""
boards_app.tests
===================

Tests for the board list/create endpoints.
"""

# Third-party
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Local
from .models import Board

User = get_user_model()


class BoardListCreateTests(APITestCase):
    """Tests for GET and POST /api/boards/."""

    def setUp(self):
        self.url = reverse("board-list-create")

        self.owner = User.objects.create_user(
            email="owner@example.com", password="pass123", fullname="Owner"
        )
        self.member = User.objects.create_user(
            email="member@example.com", password="pass123", fullname="Member"
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com", password="pass123", fullname="Outsider"
        )

        self.board = Board.objects.create(title="Existing Board", owner=self.owner)
        self.board.members.add(self.member)

    def test_list_requires_authentication(self):
        """Anonymous requests are rejected."""
        response = self.client.get(self.url)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_list_returns_only_owned_or_member_boards(self):
        """Users see boards they own or are a member of, not unrelated boards."""
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        board_ids = [board["id"] for board in response.data]
        self.assertIn(self.board.id, board_ids)

    def test_list_excludes_boards_user_has_no_access_to(self):
        """A user with no relation to a board does not see it."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url)

        board_ids = [board["id"] for board in response.data]
        self.assertNotIn(self.board.id, board_ids)

    def test_create_sets_authenticated_user_as_owner(self):
        """A new board's owner is the requesting user, not a client-supplied value."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.url, {"title": "New Board", "members": []}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner_id"], self.owner.id)
        self.assertEqual(response.data["member_count"], 0)

    def test_create_adds_specified_members(self):
        """Members passed in the request are attached to the new board."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.url,
            {"title": "Team Board", "members": [self.member.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["member_count"], 1)


class BoardDetailTests(APITestCase):
    """Tests for GET /api/boards/{board_id}/."""

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

        self.board = Board.objects.create(title="Detail Board", owner=self.owner)
        self.board.members.add(self.member)

        self.url = reverse("board-detail", kwargs={"board_id": self.board.id})

    def test_owner_can_view_board_detail(self):
        """The board's owner can retrieve its details."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.board.id)
        self.assertEqual(len(response.data["members"]), 1)

    def test_member_can_view_board_detail(self):
        """A board member (not the owner) can also retrieve its details."""
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_gets_403(self):
        """A user with no relation to the board is forbidden, not just filtered out."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_board_gets_404(self):
        """A board ID that doesn't exist at all returns 404, not 403."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("board-detail", kwargs={"board_id": 999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_gets_401(self):
        """Anonymous requests are rejected before the permission check even runs."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
