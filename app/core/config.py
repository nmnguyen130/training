from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "MockP API"
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: str = "*"

    # Database
    POSTGRES_OWNER_USER: str = "postgres"
    POSTGRES_OWNER_PASSWORD: str
    
    POSTGRES_APP_USER: str = "mockp_app"
    POSTGRES_APP_PASSWORD: str
    
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "mock_db"
    DATABASE_URL: str | None = None
    DATABASE_OWNER_URL: str | None = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_OWNER_POOL_SIZE: int = 2
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @model_validator(mode="after")
    def assemble_database_url(self):
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_APP_USER}:{self.POSTGRES_APP_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        if not self.DATABASE_OWNER_URL:
            self.DATABASE_OWNER_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_OWNER_USER}:{self.POSTGRES_OWNER_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        if self.ENVIRONMENT == "production":
            if self.ALLOWED_ORIGINS == "*":
                raise ValueError("ALLOWED_ORIGINS cannot be '*' in production")
            if len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters in production")
        return self

    @property
    def parsed_cors_origins(self) -> list[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
