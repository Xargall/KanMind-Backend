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
        return 0

    def get_tasks_to_do_count(self, obj):
        return 0

    def get_tasks_high_prio_count(self, obj):
        return 0


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
