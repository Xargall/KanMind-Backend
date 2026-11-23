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


class BoardUpdateTests(APITestCase):
    """Tests for PATCH /api/boards/{board_id}/."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner3@example.com", password="pass123", fullname="Owner3"
        )
        self.member = User.objects.create_user(
            email="member3@example.com", password="pass123", fullname="Member3"
        )
        self.outsider = User.objects.create_user(
            email="outsider3@example.com", password="pass123", fullname="Outsider3"
        )

        self.board = Board.objects.create(title="Original Title", owner=self.owner)
        self.board.members.add(self.member)

        self.url = reverse("board-detail", kwargs={"board_id": self.board.id})

    def test_owner_can_update_title_and_members(self):
        """Owner can change title and replace the members list."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.url,
            {"title": "New Title", "members": [self.outsider.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "New Title")
        self.assertEqual(response.data["owner_data"]["id"], self.owner.id)
        member_ids = [m["id"] for m in response.data["members_data"]]
        self.assertEqual(member_ids, [self.outsider.id])

    def test_member_can_also_update_board(self):
        """A board member (not just the owner) is allowed to update it."""
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(self.url, {"title": "Member Edit"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_gets_403(self):
        """A user with no relation to the board cannot update it."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.patch(self.url, {"title": "Hacked"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_title_only_keeps_members(self):
        """Sending only `title` leaves existing members untouched."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.url, {"title": "Only Title Changed"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member_ids = [m["id"] for m in response.data["members_data"]]
        self.assertEqual(member_ids, [self.member.id])

    def test_invalid_member_id_returns_400(self):
        """A non-existent user ID in `members` is rejected."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.url, {"members": [999999]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BoardDeleteTests(APITestCase):
    """Tests for DELETE /api/boards/{board_id}/."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner4@example.com", password="pass123", fullname="Owner4"
        )
        self.member = User.objects.create_user(
            email="member4@example.com", password="pass123", fullname="Member4"
        )

        self.board = Board.objects.create(title="To Delete", owner=self.owner)
        self.board.members.add(self.member)

        self.url = reverse("board-detail", kwargs={"board_id": self.board.id})

    def test_owner_can_delete_board(self):
        """The owner can delete their own board."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.filter(id=self.board.id).exists())

    def test_member_cannot_delete_board(self):
        """A member (non-owner) is forbidden from deleting the board."""
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.filter(id=self.board.id).exists())
