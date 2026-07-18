from rest_framework.permissions import BasePermission


class IsOfficer(BasePermission):
    """Law enforcement officers and admins."""
    message = 'Access restricted to law enforcement officers.'

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.role in ('officer', 'admin')
        )


class IsAdmin(BasePermission):
    """Platform admins only."""
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated and request.user.role == 'admin'
        )


class HasActiveSubscription(BasePermission):
    """User must hold an active paid subscription."""
    message = 'An active subscription is required to access this feature.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        sub = getattr(request.user, 'subscription', None)
        return bool(sub and sub.status in ('active', 'trialing') and sub.plan.name != 'free')


class IsOwnerOrAdmin(BasePermission):
    """Object-level: only the owning user or an admin may access."""

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'role', None) == 'admin':
            return True
        return getattr(obj, 'user', None) == request.user


class IsSupervisorOfAgency(BasePermission):
    """
    Object-level: the request user must be a supervisor (or admin) in the same
    agency as the document's owner. Supervisor is a capability flag on an
    existing officer account, not a separate Role (see accounts.models.User.is_supervisor).
    """
    message = 'Supervisor access (within the same agency) required.'

    def has_permission(self, request, view):
        u = request.user
        return bool(u.is_authenticated and (u.role == 'admin' or u.is_supervisor))

    def has_object_permission(self, request, view, obj):
        u = request.user
        if u.role == 'admin':
            return True
        doc_owner_agency_id = getattr(obj.user, 'agency_id', None)
        return bool(u.is_supervisor and doc_owner_agency_id and u.agency_id == doc_owner_agency_id)
