from rest_framework import permissions

from account.conf import settings

class AllowUserInitiatedSiteInvitations(permissions.BasePermission):
    """
    Permission that checks if users can send site invitations
    """

    def has_permission(self, request, view):
        return settings.ALLOW_USER_INITIATED_INVITE
