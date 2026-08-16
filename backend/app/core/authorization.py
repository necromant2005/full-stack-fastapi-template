from app.models import Permission, User, UserRole

ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.admin: frozenset(Permission),
    UserRole.manager: frozenset(
        {
            Permission.users_list,
            Permission.metrics_view,
        }
    ),
    UserRole.member: frozenset(),
}


def permissions_for_role(role: UserRole) -> list[Permission]:
    return sorted(ROLE_PERMISSIONS[role], key=str)


def has_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[user.role]
