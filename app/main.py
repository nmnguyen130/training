import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.middleware import RequestContextMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.database import app_engine, app_session, owner_engine
from app.core.exceptions import register_exception_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application %s...", settings.PROJECT_NAME)
    
    yield
    logger.info("Disposing database connection pool...")
    await app_engine.dispose()
    await owner_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# 1. Register Global Exception Handlers
register_exception_handlers(app)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. RequestContext & Tracing Middleware
app.add_middleware(RequestContextMiddleware)

# 4. Include API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


# 5. System Endpoints
@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    db_ok = False
    try:
        async with app_session() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("Database health check failed: %s", e)

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": db_ok,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": f"{settings.API_V1_STR}/docs",
    }
