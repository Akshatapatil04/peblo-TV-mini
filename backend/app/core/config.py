import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Peblo TV Mini API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Database
    # Support PostgreSQL with fallback to SQLite for local development and fast tests
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/peblo_tv"
    )
    # Sync DB URL for migrations / seeds if needed
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/peblo_tv"
    )
    
    # Storage Configuration (Abstraction: 'local' or 'r2' / 's3')
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage")))
    
    # Cloudflare R2 / S3 Configuration
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "peblo-tv-assets")
    R2_PUBLIC_URL_PREFIX: str = os.getenv("R2_PUBLIC_URL_PREFIX", "https://assets.peblo.tv")
    R2_ENDPOINT_URL: str = os.getenv("R2_ENDPOINT_URL", "")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Security / Roles
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "peblo-admin-secret-key")
    EDITOR_API_KEY: str = os.getenv("EDITOR_API_KEY", "peblo-editor-secret-key")
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
