"""
tasks_app.api.serializers
============================

Serializers for the task endpoints.
"""

# Third party
from django.contrib.auth import get_user_model
from rest_framework import serializers

# Local
from ..models import Task
from auth_app.api.serializers import PublicUserSerializer

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    """Serializes a task for responses, with nested assignee/reviewer objects."""

    assignee = PublicUserSerializer(read_only=True)
    reviewer = PublicUserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return 0


class TaskCreateSerializer(serializers.ModelSerializer):
    """Validates task creation input; assignee/reviewer must be members of the given board."""

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee", queryset=User.objects.all(), required=False, allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer", queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "due_date",
        ]

    def validate(self, attrs):
        board = attrs.get("board")
        assignee = attrs.get("assignee")
        reviewer = attrs.get("reviewer")

        def is_board_member(user):
            return user == board.owner or board.members.filter(id=user.id).exists()

        for field_name, user in (("assignee_id", assignee), ("reviewer_id", reviewer)):
            if user and not is_board_member(user):
                raise serializers.ValidationError(
                    {field_name: "User must be a member of the board."}
                )

        return attrs


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Validates partial task updates; assignee/reviewer must stay board members, board is immutable."""

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee", queryset=User.objects.all(), required=False, allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer", queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "due_date",
        ]
        extra_kwargs = {
            field: {"required": False}
            for field in ("title", "description", "status", "priority", "due_date")
        }

    def validate(self, attrs):
        board = self.instance.board
        assignee = attrs.get("assignee", self.instance.assignee)
        reviewer = attrs.get("reviewer", self.instance.reviewer)

        def is_board_member(user):
            return user == board.owner or board.members.filter(id=user.id).exists()

        for field_name, user in (("assignee_id", assignee), ("reviewer_id", reviewer)):
            if user and not is_board_member(user):
                raise serializers.ValidationError(
                    {field_name: "User must be a member of the board."}
                )

        return attrs
