from django.db import models

from ..common.models import CommonFieldModel


class Organization(CommonFieldModel):
    name = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "organization"
        verbose_name = "Organization"

    def __str__(self):
        return self.name


class UserOrganizationRoleMap(CommonFieldModel):
    user_id = models.BigIntegerField(
        null=False, blank=False, help_text="User unique identifier id"
    )
    organization = models.ForeignKey(
        "Organization", related_name="organization_role_maps", on_delete=models.CASCADE
    )
    role = models.ForeignKey(
        "Role", related_name="organization_role_maps", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "user_organization_role_map"
        verbose_name = "User Organization Role Map"

    def __str__(self):
        return (
            "User_id: "
            + str(self.user_id)
            + ", Org: "
            + self.organization.name
            + ", Role: "
            + self.role.name
        )


class Role(CommonFieldModel):
    name = models.CharField(
        max_length=255, null=False, blank=False, help_text="Role of user"
    )

    class Meta:
        db_table = "role"
        verbose_name = "Role"

    def __str__(self):
        return self.name


class OrganizationRolePermissionMap(CommonFieldModel):
    organization = models.ForeignKey(
        "Organization",
        related_name="role_permission",
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        Role, related_name="role_permission", on_delete=models.SET_NULL, null=True
    )
    permission = models.ForeignKey(
        "Permission",
        related_name="role_permission",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "organization_role_permission"
        verbose_name = "Organization Role Permission Map"

    def __str__(self):
        return (
            "Org: "
            + self.organization.name
            + ", Role: "
            + str(self.role.name)
            + ", Permission: "
            + str(self.permission.name)
        )


class Permission(CommonFieldModel):
    name = models.CharField(
        max_length=255, null=False, blank=False, help_text="Permission of Endpoints"
    )

    class Meta:
        db_table = "permission"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.name


class Activity(CommonFieldModel):
    class HttpMethodChoices(models.TextChoices):
        GET = ("GET",)
        POST = ("POST",)
        PUT = ("PUT",)
        DELETE = "DELETE"

    api_path = models.CharField(
        max_length=255, null=False, blank=False, help_text="API relative path"
    )
    http_method = models.CharField(
        max_length=10,
        choices=HttpMethodChoices.choices,
        null=False,
        blank=False,
        help_text="HTTP method e.g. GET, POST",
    )
    url_regex = models.CharField(
        max_length=255, null=True, blank=True, help_text="Regex of the api endpoint"
    )

    class Meta:
        db_table = "activity"
        verbose_name = "Activity"
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.api_path


class PermissionActivity(CommonFieldModel):
    permission = models.ForeignKey(
        Permission, related_name="permission_activity", on_delete=models.CASCADE
    )
    activity = models.ForeignKey(
        Activity, related_name="permission_activity", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "permission_activity"
        verbose_name = "Activity Permission Map"
        verbose_name_plural = "Activity Permission Maps"

    def __str__(self):
        return (
            "Permission: "
            + self.permission.name
            + ",  Activity: "
            + self.activity.api_path
        )
