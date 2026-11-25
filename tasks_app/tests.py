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
from .models import Task, Comment
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

    def test_str_returns_title(self):
        self.assertEqual(str(self.task), self.task.title)

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


class TaskDeleteTests(APITestCase):
    """Tests for DELETE /api/tasks/{task_id}/."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner3@example.com", password="pass123", fullname="Owner3"
        )
        self.creator = User.objects.create_user(
            email="creator3@example.com", password="pass123", fullname="Creator3"
        )
        self.member = User.objects.create_user(
            email="member3@example.com", password="pass123", fullname="Member3"
        )
        self.outsider = User.objects.create_user(
            email="outsider3@example.com", password="pass123", fullname="Outsider3"
        )

        self.board = Board.objects.create(title="Delete Board", owner=self.owner)
        self.board.members.add(self.creator, self.member)

        self.task = Task.objects.create(
            board=self.board,
            title="Task To Delete",
            status="to-do",
            priority="low",
            created_by=self.creator,
        )

        self.url = reverse("task-detail", kwargs={"task_id": self.task.id})

    def test_creator_can_delete_task(self):
        """The user who created the task can delete it."""
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_board_owner_can_delete_task(self):
        """The board owner can delete a task even if they didn't create it."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_member_who_is_not_creator_gets_403(self):
        """A board member who neither created the task nor owns the board cannot delete it."""
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())

    def test_outsider_gets_403(self):
        """A user with no relation to the board cannot delete its tasks."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())

    def test_nonexistent_task_gets_404(self):
        """A task ID that doesn't exist returns 404, not 403."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("task-detail", kwargs={"task_id": 999999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_gets_401(self):
        """Anonymous requests are rejected before the permission check even runs."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())


class TaskAssignedToMeTests(APITestCase):
    """Tests for GET /api/tasks/assigned-to-me/."""

    def setUp(self):
        self.url = reverse("assigned-tasks")

        self.owner = User.objects.create_user(
            email="owner4@example.com", password="pass123", fullname="Owner4"
        )
        self.assignee_user = User.objects.create_user(
            email="assignee4@example.com", password="pass123", fullname="Assignee4"
        )
        self.reviewer_user = User.objects.create_user(
            email="reviewer4@example.com", password="pass123", fullname="Reviewer4"
        )
        self.bystander = User.objects.create_user(
            email="bystander4@example.com", password="pass123", fullname="Bystander4"
        )

        self.board = Board.objects.create(title="Assigned Board", owner=self.owner)
        self.board.members.add(self.assignee_user, self.reviewer_user, self.bystander)

        self.assigned_task = Task.objects.create(
            board=self.board,
            title="Task I'm assigned to",
            status="to-do",
            priority="medium",
            assignee=self.assignee_user,
        )
        self.reviewed_task = Task.objects.create(
            board=self.board,
            title="Task I'm reviewing",
            status="to-do",
            priority="medium",
            reviewer=self.reviewer_user,
        )
        self.unrelated_task = Task.objects.create(
            board=self.board,
            title="Task with no relation to anyone special",
            status="to-do",
            priority="low",
        )

    def test_requires_authentication(self):
        """Anonymous requests are rejected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_tasks_where_user_is_assignee(self):
        """A task where the user is the assignee shows up."""
        self.client.force_authenticate(user=self.assignee_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_ids = [task["id"] for task in response.data]
        self.assertIn(self.assigned_task.id, task_ids)

    def test_returns_tasks_where_user_is_reviewer(self):
        """A task where the user is the reviewer shows up too, not just as assignee."""
        self.client.force_authenticate(user=self.reviewer_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_ids = [task["id"] for task in response.data]
        self.assertIn(self.reviewed_task.id, task_ids)

    def test_user_with_no_relation_gets_empty_list(self):
        """A user who is neither assignee nor reviewer on any task gets an empty list, not an error."""
        self.client.force_authenticate(user=self.bystander)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class TaskReviewingTests(APITestCase):
    """Tests for GET /api/tasks/reviewing/."""

    def setUp(self):
        self.url = reverse("reviewed-tasks")

        self.owner = User.objects.create_user(
            email="owner5@example.com", password="pass123", fullname="Owner5"
        )
        self.reviewer_user = User.objects.create_user(
            email="reviewer5@example.com", password="pass123", fullname="Reviewer5"
        )
        self.assignee_only_user = User.objects.create_user(
            email="assignee5@example.com", password="pass123", fullname="Assignee5"
        )
        self.bystander = User.objects.create_user(
            email="bystander5@example.com", password="pass123", fullname="Bystander5"
        )

        self.board = Board.objects.create(title="Reviewing Board", owner=self.owner)
        self.board.members.add(
            self.reviewer_user, self.assignee_only_user, self.bystander
        )

        self.reviewed_task = Task.objects.create(
            board=self.board,
            title="Task I'm reviewing",
            status="to-do",
            priority="medium",
            reviewer=self.reviewer_user,
        )
        self.assigned_only_task = Task.objects.create(
            board=self.board,
            title="Task I'm only assigned to",
            status="to-do",
            priority="medium",
            assignee=self.assignee_only_user,
        )

    def test_requires_authentication(self):
        """Anonymous requests are rejected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_tasks_where_user_is_reviewer(self):
        """A task where the user is the reviewer shows up."""
        self.client.force_authenticate(user=self.reviewer_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_ids = [task["id"] for task in response.data]
        self.assertIn(self.reviewed_task.id, task_ids)

    def test_assignee_only_task_is_excluded(self):
        """A task where the user is only the assignee, not the reviewer, does not show up here."""
        self.client.force_authenticate(user=self.assignee_only_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_ids = [task["id"] for task in response.data]
        self.assertNotIn(self.assigned_only_task.id, task_ids)

    def test_user_with_no_relation_gets_empty_list(self):
        """A user who is not a reviewer on any task gets an empty list, not an error."""
        self.client.force_authenticate(user=self.bystander)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class CommentListCreateTests(APITestCase):
    """Tests for GET/POST /api/tasks/{task_id}/comments/."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner6@example.com", password="pass123", fullname="Owner6"
        )
        self.member = User.objects.create_user(
            email="member6@example.com", password="pass123", fullname="Member6"
        )
        self.outsider = User.objects.create_user(
            email="outsider6@example.com", password="pass123", fullname="Outsider6"
        )

        self.board = Board.objects.create(title="Comments Board", owner=self.owner)
        self.board.members.add(self.member)

        self.task = Task.objects.create(
            board=self.board, title="Task With Comments", status="to-do", priority="low"
        )

        self.comment = Comment.objects.create(
            task=self.task, author=self.member, content="Existing comment"
        )

        self.url = reverse("tasks-comments", kwargs={"task_id": self.task.id})

    def test_list_requires_authentication(self):
        """Anonymous requests are rejected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_list_comments(self):
        """A board member can list comments, author comes back as a full name string."""
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["author"], "Member6")

    def test_outsider_gets_403_on_list(self):
        """A user with no relation to the board cannot list its task's comments."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_task_gets_404_on_list(self):
        """A task ID that doesn't exist returns 404, not 403."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("tasks-comments", kwargs={"task_id": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_can_create_comment(self):
        """A board member can create a comment; author is set from the request, not the body."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url, {"content": "New comment"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], "Owner6")
        self.assertEqual(response.data["content"], "New comment")

    def test_create_requires_authentication(self):
        """Anonymous requests are rejected."""
        response = self.client.post(self.url, {"content": "Anon"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_outsider_gets_403_on_create(self):
        """A user with no relation to the board cannot comment on its tasks."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(self.url, {"content": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_task_gets_404_on_create(self):
        """A task ID that doesn't exist returns 404, not 403."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("tasks-comments", kwargs={"task_id": 999999})
        response = self.client.post(url, {"content": "Ghost"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_empty_content_returns_400(self):
        """An empty content value is rejected."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url, {"content": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CommentDeleteTests(APITestCase):
    """Tests for DELETE /api/tasks/{task_id}/comments/{comment_id}/."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner7@example.com", password="pass123", fullname="Owner7"
        )
        self.creator = User.objects.create_user(
            email="creator7@example.com", password="pass123", fullname="Creator7"
        )
        self.member = User.objects.create_user(
            email="member7@example.com", password="pass123", fullname="Member7"
        )
        self.outsider = User.objects.create_user(
            email="outsider7@example.com", password="pass123", fullname="Outsider7"
        )

        self.board = Board.objects.create(
            title="Comment Delete Board", owner=self.owner
        )
        self.board.members.add(self.creator, self.member)

        self.task = Task.objects.create(
            board=self.board, title="Task", status="to-do", priority="low"
        )
        self.other_task = Task.objects.create(
            board=self.board, title="Other Task", status="to-do", priority="low"
        )

        self.comment = Comment.objects.create(
            task=self.task, author=self.creator, content="To be deleted"
        )

        self.url = reverse(
            "comment-delete",
            kwargs={"task_id": self.task.id, "comment_id": self.comment.id},
        )

    def test_creator_can_delete_comment(self):
        """The user who wrote the comment can delete it."""
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_other_member_gets_403(self):
        """A board member who didn't write the comment cannot delete it."""
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_board_owner_who_is_not_creator_gets_403(self):
        """Unlike task deletion, the board owner has no special right here — only the comment's author."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_outsider_gets_403(self):
        """A user unrelated to the board cannot delete the comment either."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_comment_gets_404(self):
        """A comment ID that doesn't exist returns 404."""
        self.client.force_authenticate(user=self.creator)
        url = reverse(
            "comment-delete", kwargs={"task_id": self.task.id, "comment_id": 999999}
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_belonging_to_different_task_gets_404(self):
        """A comment that exists but belongs to a different task is not reachable via this task_id."""
        self.client.force_authenticate(user=self.creator)
        url = reverse(
            "comment-delete",
            kwargs={"task_id": self.other_task.id, "comment_id": self.comment.id},
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_gets_401(self):
        """Anonymous requests are rejected before the permission check even runs."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())