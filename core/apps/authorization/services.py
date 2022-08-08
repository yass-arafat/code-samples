import re

from .models import (
    Activity,
    OrganizationRolePermissionMap,
    PermissionActivity,
    UserOrganizationRoleMap,
)


def get_relative_path(full_url):
    return full_url.split("?", 1)[0]


class AuthorizationService:
    @classmethod
    def is_authorized(cls, user_id, api_full_path, http_method):
        api_relative_path = get_relative_path(api_full_path)
        organization_role_ids = UserOrganizationRoleMap.objects.filter(
            user_id=user_id, is_active=True
        ).values("organization", "role")
        for org_role in organization_role_ids:
            org, role = org_role["organization"], org_role["role"]
            permission_ids = OrganizationRolePermissionMap.objects.filter(
                organization__id=org, role__id=role, is_active=True
            ).values_list("permission", flat=True)
            activity_ids = PermissionActivity.objects.filter(
                permission__in=permission_ids, is_active=True
            ).values_list("activity", flat=True)
            activities = Activity.objects.filter(id__in=activity_ids)

            for activity in activities:
                pattern = re.compile(activity.url_regex)
                if (
                    pattern.match(api_relative_path)
                    and http_method == activity.http_method
                ):
                    return True
        return False
