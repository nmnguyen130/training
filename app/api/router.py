from fastapi import APIRouter

from app.modules.auth.router import auth_router, users_router
from app.modules.parties.router import (
    customers_router,
    parties_router,
    suppliers_router,
)
from app.modules.products.router import router as products_router

api_router = APIRouter()

# Auth & Users
api_router.include_router(auth_router)
api_router.include_router(users_router)

# Parties & Roles
api_router.include_router(parties_router)
api_router.include_router(customers_router)
api_router.include_router(suppliers_router)

# Business Modules
api_router.include_router(products_router)
