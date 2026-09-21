from collections.abc import Set

from app.core.exceptions import ServiceError
from app.modules.rbac.constants import FIELD_PERMISSIONS, Role


def check_field_permissions(
    resource: str,
    action: str,
    role_code: str | None,
    fields: Set[str],
) -> None:
    """Validate that the given role has permission to modify the specified fields."""
    if not fields or role_code == Role.SUPER_ADMIN:
        return

    allowed = FIELD_PERMISSIONS.get(f"{resource}.{action}", {}).get(role_code, frozenset())
    forbidden = fields - allowed
    if forbidden:
        raise ServiceError.forbidden(f"Not allowed to modify field(s): {sorted(forbidden)}")
