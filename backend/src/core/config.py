from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "Front Office Analytics Platform"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    
    api_prefix: str = "/api/v1"
    
    database_url: str = Field(
        default="postgresql+asyncpg://fo_user:fo_password@localhost:5432/fo_analytics",
        description="PostgreSQL connection string"
    )
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens"
    )
    
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for uploaded files"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()