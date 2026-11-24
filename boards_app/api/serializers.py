"""
boards_app.api.serializers
============================

Serializers for the board endpoints.
"""

# Third party
from django.contrib.auth import get_user_model
from rest_framework import serializers

# Local
from ..models import Board
from auth_app.api.serializers import PublicUserSerializer
from tasks_app.api.serializers import TaskSerializer

User = get_user_model()


class BoardListSerializer(serializers.ModelSerializer):
    """Serializes boards for the list endpoint (GET /api/boards/)."""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()


class BoardCreateSerializer(serializers.ModelSerializer):
    """Validates board creation input; owner is taken from the request, never from the client."""

    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )

    class Meta:
        model = Board
        fields = ["title", "members"]

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        owner = self.context["request"].user

        board = Board.objects.create(owner=owner, **validated_data)
        if members:
            board.members.set(members)
        return board


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializes a single board with nested members and its tasks (GET /api/boards/{board_id}/)."""

    owner_id = serializers.IntegerField(read_only=True)
    members = PublicUserSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]

    def get_tasks(self, obj):
        return TaskSerializer(obj.tasks.all(), many=True).data


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Validates board updates and returns nested owner/member data (PATCH /api/boards/{board_id}/)."""

    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False, write_only=True
    )
    owner_data = PublicUserSerializer(source="owner", read_only=True)
    members_data = PublicUserSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data", "members"]
        extra_kwargs = {"title": {"required": False}}

    def update(self, instance, validated_data):
        members = validated_data.pop("members", None)
        instance.title = validated_data.get("title", instance.title)
        instance.save()

        if members is not None:
            instance.members.set(members)

        return instance
