from app.core.database import Base
from app.modules.auth.model import User
from app.modules.products.model import Product

metadata = Base.metadata

__all__ = [
    "Base",
    "metadata",
    "User",
    "Product",
]
