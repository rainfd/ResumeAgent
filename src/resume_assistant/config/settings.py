"""Application settings and configuration management."""

from pathlib import Path
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # AI Service Configuration
    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", 
        description="DeepSeek API base URL"
    )
    
    # Database Configuration
    database_path: Path = Field(
        default_factory=lambda: Path.home() / ".resume_assistant" / "data.db",
        description="SQLite database file path"
    )
    
    # Cache Configuration
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".resume_assistant" / "cache",
        description="Cache directory path"
    )
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Scraper Configuration
    request_timeout: int = Field(default=30, description="HTTP request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # UI Configuration
    theme: str = Field(default="dark", description="UI theme")
    auto_save: bool = Field(default=True, description="Enable auto save")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(
        default_factory=lambda: Path.home() / ".resume_assistant" / "logs" / "app.log",
        description="Log file path"
    )
    
    @validator("deepseek_api_key")
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if v and not v.startswith("sk-"):
            raise ValueError("DeepSeek API key should start with 'sk-'")
        return v
    
    @validator("theme")
    def validate_theme(cls, v: str) -> str:
        """Validate theme value."""
        valid_themes = ["dark", "light"]
        if v not in valid_themes:
            raise ValueError(f"Theme must be one of: {valid_themes}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v
    
    @validator("database_path", "cache_dir", "log_file", pre=True)
    def expand_path(cls, v) -> Path:
        """Expand user path and create parent directories."""
        if isinstance(v, str):
            v = Path(v)
        if isinstance(v, Path):
            v = v.expanduser().resolve()
            # Create parent directory if it doesn't exist
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_prefix = "RESUME_ASSISTANT_"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment and config files."""
    global settings
    settings = Settings()
    return settings