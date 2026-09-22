from enum import StrEnum


class Role(StrEnum):
    SUPER_ADMIN = "super_admin"
    WAREHOUSE_MANAGER = "warehouse_manager"
    WAREHOUSE_STAFF = "warehouse_staff"
    SALES_STAFF = "sales_staff"


CRUD = (
    "read",
    "create",
    "update",
    "delete",
)

RESOURCES = (
    "product",
    "party",
    "customer",
    "supplier",
    "role",
    "user",
    "permission",
    "warehouse",
    "inventory",
)

ALL_PERMISSIONS = [f"{r}.{a}" for r in RESOURCES for a in CRUD]


SYSTEM_ROLES = {
    Role.SUPER_ADMIN: {
        "role_name": "Super Administrator",
        "description": "Full access to all system functions",
        "is_system": True,
        "permissions": {},
    },
    Role.WAREHOUSE_MANAGER: {
        "role_name": "Warehouse Manager",
        "description": "Manages warehouse layout, product catalog, inventory, and suppliers",
        "is_system": True,
        "permissions": {
            "product": CRUD,
            "warehouse": CRUD,
            "inventory": CRUD,
            "supplier": CRUD,
            "party": ("read",),
            "customer": ("read",),
        },
    },
    Role.WAREHOUSE_STAFF: {
        "role_name": "Warehouse Staff",
        "description": "Performs warehouse operations, stock transfers, and catalog lookup",
        "is_system": True,
        "permissions": {
            "product": ("read",),
            "warehouse": ("read",),
            "inventory": ("read", "create", "update"),
        },
    },
    Role.SALES_STAFF: {
        "role_name": "Sales Staff",
        "description": "Manages customers and views product catalog",
        "is_system": True,
        "permissions": {
            "customer": ("read", "create", "update"),
            "product": ("read",),
            "party": ("read",),
            "inventory": ("read",),
        },
    },
}


# Field write permissions: "{resource}.{action}" -> {role_code: frozenset(allowed_fields)}.
# Fail-closed for unlisted roles; SUPER_ADMIN bypasses.
FIELD_PERMISSIONS: dict[str, dict[str, frozenset[str]]] = {
    "party.update": {
        Role.WAREHOUSE_MANAGER.value: frozenset({
            "party_type",
            "display_name",
            "phone",
            "email",
            "address",
            "is_active",
        }),
        Role.SALES_STAFF.value: frozenset({
            "phone",
            "email",
            "address",
        }),
    },
}
