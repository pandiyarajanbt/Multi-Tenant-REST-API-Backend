from rest_framework import serializers
from apps.accounts.models import Organization, User
from .models import Project, Invitation


class OrganizationSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source="members.count", read_only=True)

    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "is_active", "member_count", "created_at")
        read_only_fields = ("id", "created_at")


class ProjectSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = Project
        fields = ("id", "name", "description", "status", "created_by_email", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "created_by_email")


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "created_at")
        read_only_fields = fields


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ("id", "email", "role", "status", "created_at")
        read_only_fields = ("id", "status", "created_at")
