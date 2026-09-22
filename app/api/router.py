from fastapi import APIRouter

from app.modules.auth.router import auth_router, users_router
from app.modules.inventory.router import router as inventory_router
from app.modules.parties.router import (
    customers_router,
    parties_router,
    suppliers_router,
)
from app.modules.products.router import router as products_router
from app.modules.rbac.router import (
    permissions_router,
    roles_router,
    user_roles_router,
)
from app.modules.warehouse.router import router as warehouse_router

api_router = APIRouter()

# Auth & Users
api_router.include_router(auth_router)
api_router.include_router(users_router)

# RBAC
api_router.include_router(roles_router)
api_router.include_router(permissions_router)
api_router.include_router(user_roles_router)

# Parties Management
api_router.include_router(parties_router)
api_router.include_router(customers_router)
api_router.include_router(suppliers_router)

# Warehouse Management
api_router.include_router(products_router)
api_router.include_router(warehouse_router)
api_router.include_router(inventory_router)
