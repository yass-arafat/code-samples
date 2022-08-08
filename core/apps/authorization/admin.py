from django.contrib import admin

from .models import (
    Activity,
    Organization,
    OrganizationRolePermissionMap,
    Permission,
    PermissionActivity,
    Role,
    UserOrganizationRoleMap,
)

admin.site.register(
    [
        Organization,
        UserOrganizationRoleMap,
        Role,
        OrganizationRolePermissionMap,
        Activity,
        Permission,
        PermissionActivity,
    ]
)
