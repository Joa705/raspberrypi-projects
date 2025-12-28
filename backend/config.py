"""
Configuration management for the camera backend.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    app_name: str = "Raspberry Pi FastAPI backend"
    debug: bool = False
    
    host: str = "localhost"
    port: int = 8000
    
    database_url: str = "sqlite+aiosqlite:///./database/sqlite.db"
    
    log_level: str = "INFO"
    
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin"
    
    secret_key: str = "your_secret_key"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 12
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
