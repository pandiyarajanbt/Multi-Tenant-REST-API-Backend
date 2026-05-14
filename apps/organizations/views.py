from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.models import Organization, User
from apps.core.permissions import IsOrgAdmin, IsOrgMember, IsSameTenant
from .models import Project, Invitation
from .serializers import (
    OrganizationSerializer, ProjectSerializer, MemberSerializer, InvitationSerializer
)

CACHE_TTL = 60 * 5  # 5 minutes


class TenantQuerysetMixin:
    """Restrict querysets to the authenticated user's organization."""

    def get_tenant_qs(self, model):
        return model.objects.filter(organization=self.request.user.organization)


# ── Organizations ──────────────────────────────────────────────────────────────

class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgMember)

    def get_object(self):
        org = self.request.user.organization
        self.check_object_permissions(self.request, org)
        return org

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [permissions.IsAuthenticated(), IsOrgAdmin()]
        return super().get_permissions()


# ── Projects ───────────────────────────────────────────────────────────────────

@method_decorator(cache_page(CACHE_TTL), name="list")
@method_decorator(vary_on_headers("Authorization"), name="list")
class ProjectListCreateView(TenantQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgMember)
    filterset_fields = ("status",)
    search_fields = ("name", "description")
    ordering_fields = ("created_at", "name")

    def get_queryset(self):
        return self.get_tenant_qs(Project).select_related("created_by", "organization")

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization, created_by=self.request.user)


class ProjectDetailView(TenantQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgMember, IsSameTenant)

    def get_queryset(self):
        return self.get_tenant_qs(Project)

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [permissions.IsAuthenticated(), IsOrgAdmin()]
        return super().get_permissions()


# ── Members ────────────────────────────────────────────────────────────────────

@method_decorator(cache_page(CACHE_TTL), name="get")
@method_decorator(vary_on_headers("Authorization"), name="get")
class MemberListView(generics.ListAPIView):
    serializer_class = MemberSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgMember)
    search_fields = ("email", "full_name")
    filterset_fields = ("role",)

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization)


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MemberSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgAdmin)

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization)

    def partial_update(self, request, *args, **kwargs):
        # Only allow role updates
        allowed = {k: v for k, v in request.data.items() if k == "role"}
        serializer = self.get_serializer(self.get_object(), data=allowed, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Invitations ────────────────────────────────────────────────────────────────

class InvitationListCreateView(generics.ListCreateAPIView):
    serializer_class = InvitationSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgAdmin)

    def get_queryset(self):
        return Invitation.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            invited_by=self.request.user,
        )
