"""
boards_app.api.serializers
============================

Serializers for the board endpoints.
"""

# Third party
from rest_framework import serializers

# Local
from ..models import Board


class BoardListSerializer(serializers.ModelSerializer):
    """Serializes boards for the list endpoint (GET /api/boards/)."""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source="owner_id", read_only=True)

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

    def get_tasksto_do_count(self, obj):
        return 0

    def get_tasks_high_prio_count(self, obj):
        return 0
