from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Agency, JurisdictionProfile


@admin.register(JurisdictionProfile)
class JurisdictionProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'jurisdiction_type', 'state', 'county')
    search_fields = ('name', 'state', 'county')
    list_filter = ('jurisdiction_type',)


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'jurisdiction_type', 'jurisdiction_profile', 'state', 'county',
        'requires_supervisor_review', 'requires_prosecutor_review',
    )
    search_fields = ('name', 'state', 'county', 'ori')
    list_filter = ('jurisdiction_type', 'state', 'requires_supervisor_review', 'requires_prosecutor_review')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for the email-based custom User (no username field)."""

    ordering = ('-created_at',)
    list_display = (
        'email', 'role', 'agency', 'department_name', 'is_supervisor',
        'email_verified', 'is_staff', 'is_active',
    )
    list_filter = ('role', 'email_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'badge_number', 'department_name', 'ori')
    readonly_fields = ('created_at', 'updated_at', 'last_active')

    # Rebuilt for email login (Django's defaults assume a username field).
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Role & verification', {
            'fields': ('role', 'email_verified')
        }),
        ('Officer profile', {
            'fields': (
                'agency', 'is_supervisor', 'badge_number', 'department_name', 'department_address',
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
