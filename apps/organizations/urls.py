from django.urls import path
from .views import (
    OrganizationDetailView,
    ProjectListCreateView,
    ProjectDetailView,
    MemberListView,
    MemberDetailView,
    InvitationListCreateView,
)

urlpatterns = [
    path("organization/", OrganizationDetailView.as_view(), name="org-detail"),
    path("projects/", ProjectListCreateView.as_view(), name="project-list"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("members/", MemberListView.as_view(), name="member-list"),
    path("members/<int:pk>/", MemberDetailView.as_view(), name="member-detail"),
    path("invitations/", InvitationListCreateView.as_view(), name="invitation-list"),
]
