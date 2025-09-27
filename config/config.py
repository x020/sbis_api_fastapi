"""
Configuration management for SBIS API FastAPI application.
"""
import os
from typing import List, Optional

from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ServerSettings(BaseSettings):
    """Server configuration settings."""

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    environment: str = "development"
    reload: bool = True

    class Config:
        env_prefix = "SERVER_"


class SabySettings(BaseSettings):
    """Saby CRM API configuration settings."""

    app_client_id: str
    app_secret: str
    secret_key: str
    base_url: str = "https://online.sbis.ru"
    auth_url: str = "https://online.sbis.ru/oauth/service/"
    api_url: str = "https://online.sbis.ru/service/"
    request_timeout: int = 30

    class Config:
        env_prefix = "SABY_"

    @validator("app_client_id", "app_secret", "secret_key")
    def validate_saby_credentials(cls, v):
        """Validate that Saby credentials are provided."""
        if not v:
            raise ValueError("Saby CRM credentials must be provided")
        return v


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    secret_key: str = "your-secret-key-change-this-in-production"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    class Config:
        env_prefix = ""


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "json"
    file_path: str = "logs/app.log"
    max_file_size: str = "10 MB"
    backup_count: int = 5

    class Config:
        env_prefix = "LOG_"


class CORSSettings(BaseSettings):
    """CORS configuration settings."""

    origins: List[str] = ["http://localhost:3000"]
    methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    headers: List[str] = ["*"]
    credentials: bool = True

    class Config:
        env_prefix = "CORS_"


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration settings."""

    requests_per_minute: int = 60
    burst: int = 10

    class Config:
        env_prefix = "RATE_LIMIT_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    url: str = "redis://localhost:6379"
    cache_ttl: int = 300

    class Config:
        env_prefix = "REDIS_"


class FeatureFlags(BaseSettings):
    """Feature flags configuration."""

    create_deal: bool = True
    update_deal: bool = True
    delete_deal: bool = False
    bulk_operations: bool = True

    class Config:
        env_prefix = "FEATURE_"


class DomainSettings(BaseSettings):
    """Domain configuration settings."""

    domain: str = "sabby.ru"
    api_port: int = 8000

    class Config:
        env_prefix = ""


class Settings(BaseSettings):
    """Main application settings."""

    domain: DomainSettings = DomainSettings()
    server: ServerSettings = ServerSettings()
    saby: SabySettings
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    cors: CORSSettings = CORSSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    redis: RedisSettings = RedisSettings()
    features: FeatureFlags = FeatureFlags()

    class Config:
        case_sensitive = True


# Global settings instance
settings = Settings(
    saby=SabySettings(),
    _env_file=".env",
    _env_file_encoding="utf-8"
)


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def create_directories():
    """Create necessary directories for the application."""
    directories = [
        "logs",
        "backups",
        settings.logging.file_path.rsplit("/", 1)[0] if "/" in settings.logging.file_path else ".",
    ]

    for directory in directories:
        if directory and directory != ".":
            os.makedirs(directory, exist_ok=True)


# Create directories on import
create_directories()