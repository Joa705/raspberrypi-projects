"""
Configuration management for the camera backend.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    app_name: str = "Raspberry Pi central backend"
    debug: bool = False
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    database_url: str = "sqlite+aiosqlite:///./database/sqlite.db"
    
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    max_camera_frame_size: int = 5242880  # 5MB
    
    log_level: str = "INFO"
    
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
