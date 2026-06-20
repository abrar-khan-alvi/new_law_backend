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


class IsVerifiedOfficer(BasePermission):
    """Officers who have been vetted/approved by an admin."""
    message = 'Your officer account is pending admin verification.'

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u.is_authenticated
            and u.role in ('officer', 'admin')
            and (u.is_verified or u.role == 'admin')
        )


class HasActiveSubscription(BasePermission):
    """User must hold an active paid subscription."""
    message = 'An active subscription is required to access this feature.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        sub = getattr(request.user, 'subscription', None)
        return bool(sub and sub.status == 'active' and sub.plan.name != 'free')


class HasDocumentQuota(BasePermission):
    """User has not exceeded their monthly document generation limit."""
    message = 'Monthly document generation limit reached. Please upgrade your plan.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.can_generate_document


class IsOwnerOrAdmin(BasePermission):
    """Object-level: only the owning user or an admin may access."""

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'role', None) == 'admin':
            return True
        return getattr(obj, 'user', None) == request.user
