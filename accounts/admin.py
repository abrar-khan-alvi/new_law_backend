from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for the email-based custom User (no username field)."""

    ordering = ('-created_at',)
    list_display = (
        'email', 'role', 'department_name',
        'email_verified', 'is_verified', 'is_staff', 'is_active',
    )
    list_filter = ('role', 'email_verified', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'badge_number', 'department_name', 'ori')
    readonly_fields = ('created_at', 'updated_at', 'last_active', 'verified_at')

    # Rebuilt for email login (Django's defaults assume a username field).
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Role & verification', {
            'fields': ('role', 'email_verified', 'is_verified', 'verified_at', 'verified_by')
        }),
        ('Officer profile', {
            'fields': (
                'badge_number', 'department_name', 'department_address',
                'department_state', 'ori', 'phone_number', 'rank', 'division',
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Activity', {'fields': ('last_active', 'last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
