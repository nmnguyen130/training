from fastapi import APIRouter

from app.modules.auth.router import auth_router, users_router
from app.modules.products.router import router as products_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(products_router)
