"""Role and permission constants for Warehouse Management System (WMS)."""

# List of all standard system permissions: (permission_code, description)
SYSTEM_PERMISSIONS = [
    # System Administration
    ("system.admin", "Full system administrator master bypass"),
    ("user.manage", "Manage user accounts and role assignments"),
    ("role.manage", "Manage roles and permission mappings"),
    ("permission.manage", "Manage system permissions"),
    # Parties (Customers & Suppliers)
    ("party.read", "View party entities"),
    ("party.manage", "Create and update general parties"),
    ("customer.read", "View customer records"),
    ("customer.manage", "Create and update customers"),
    ("supplier.read", "View supplier records"),
    ("supplier.manage", "Create and update suppliers"),
    # Products Catalog
    ("product.read", "View product catalog, pricing, and details"),
    ("product.manage", "Create, update, and manage product catalog"),
    # Warehouse & Inventory Operations
    ("inventory.read", "View stock levels, locations, and inventory metrics"),
    ("inventory.manage", "Perform inventory adjustments, transfers, and cycle counts"),
    ("inbound.manage", "Manage and process inbound receiving and put-away"),
    ("outbound.manage", "Manage and process picking, packing, and dispatch"),
]

# System Roles definitions and their default permission mappings
SYSTEM_ROLES = {
    "super_admin": {
        "role_name": "Super Administrator",
        "description": "Full access to all system functions and configurations",
        "is_system": True,
        "permissions": [code for code, _ in SYSTEM_PERMISSIONS],
    },
    "warehouse_manager": {
        "role_name": "Warehouse Manager",
        "description": "Manages warehouse operations, inventory adjustments, suppliers, and catalog",
        "is_system": True,
        "permissions": [
            "party.read",
            "customer.read",
            "supplier.read",
            "supplier.manage",
            "product.read",
            "product.manage",
            "inventory.read",
            "inventory.manage",
            "inbound.manage",
            "outbound.manage",
        ],
    },
    "warehouse_staff": {
        "role_name": "Warehouse Staff",
        "description": "Performs warehouse inbound receiving, outbound fulfillment, and stock checks",
        "is_system": True,
        "permissions": [
            "product.read",
            "inventory.read",
            "inbound.manage",
            "outbound.manage",
        ],
    },
    "sales_staff": {
        "role_name": "Sales Staff",
        "description": "Handles customer accounts, views catalog and stock levels, requests outbound dispatch",
        "is_system": True,
        "permissions": [
            "party.read",
            "customer.read",
            "customer.manage",
            "product.read",
            "inventory.read",
            "outbound.manage",
        ],
    },
}
