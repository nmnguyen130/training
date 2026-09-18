# Standard system permissions (resource.action)
ALL_PERMISSIONS = [
    # Products
    "product.read",
    "product.create",
    "product.update",
    "product.delete",

    # Parties
    "party.read",
    "party.create",
    "party.update",
    "party.delete",

    # Customers
    "customer.read",
    "customer.create",
    "customer.update",
    "customer.delete",

    # Suppliers
    "supplier.read",
    "supplier.create",
    "supplier.update",
    "supplier.delete",

    # Roles & Users
    "role.read",
    "role.create",
    "role.update",
    "role.delete",
    "user.read",
    "user.update",
    "permission.read",
]


SYSTEM_ROLES = {
    "super_admin": {
        "role_name": "Super Administrator",
        "description": "Full access to all system functions",
        "is_system": True,
        "permissions": ALL_PERMISSIONS,
    },
    "warehouse_manager": {
        "role_name": "Warehouse Manager",
        "description": "Manages product catalog and suppliers",
        "is_system": True,
        "permissions": [
            "product.read",
            "product.create",
            "product.update",
            "product.delete",
            "supplier.read",
            "supplier.create",
            "supplier.update",
            "supplier.delete",
            "party.read",
            "customer.read",
        ],
    },
    "warehouse_staff": {
        "role_name": "Warehouse Staff",
        "description": "Performs warehouse operations and catalog lookup",
        "is_system": True,
        "permissions": [
            "product.read",
        ],
    },
    "sales_staff": {
        "role_name": "Sales Staff",
        "description": "Manages customers and views product catalog",
        "is_system": True,
        "permissions": [
            "product.read",
            "party.read",
            "customer.read",
            "customer.create",
            "customer.update",
        ],
    },
}
