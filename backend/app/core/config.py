from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PIM API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./pim_new.db"
    RUN_DB_INIT: bool = True

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Redis (prepared for Celery in future phases)
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Admin seed
    ADMIN_EMAIL: str = "admin@pim.local"
    ADMIN_PASSWORD: str = "admin"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
