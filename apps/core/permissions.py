from rest_framework.permissions import BasePermission


class IsOrgAdmin(BasePermission):
    """Allow access only to users with the 'admin' role in their organization."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsOrgMember(BasePermission):
    """Allow access to any authenticated member of an organization."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.organization_id is not None


class IsSameTenant(BasePermission):
    """Object-level: ensure the object belongs to the requesting user's tenant."""

    def has_object_permission(self, request, view, obj):
        return obj.organization_id == request.user.organization_id
