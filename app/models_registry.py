from app.core.database import Base
from app.modules.auth.model import UserAccount
from app.modules.inventory.model import Inventory, InventoryMovement
from app.modules.parties.model import Customer, Party, Supplier
from app.modules.products.model import Product
from app.modules.rbac.model import Permission, Role, RolePermission, UserRole
from app.modules.warehouse.model import Location, Warehouse

metadata = Base.metadata

__all__ = [
    "Base",
    "metadata",
    "UserAccount",
    "UserRole",
    "Role",
    "RolePermission",
    "Permission",
    "Party",
    "Customer",
    "Supplier",
    "Product",
    "Warehouse",
    "Location",
    "Inventory",
    "InventoryMovement",
]
