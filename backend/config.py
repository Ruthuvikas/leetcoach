import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./leetcoach.db"
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # OpenAI
    openai_api_key: str = ""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Logging
    log_level: str = "INFO"
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        # Skip validation in test environment or if explicitly set to allow default
        if os.getenv("TESTING") == "true" or os.getenv("ALLOW_DEFAULT_SECRET") == "true":
            return v
        if v == "your-super-secret-key-change-this-in-production":
            raise ValueError("Please change the default secret key in production")
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v):
        # Skip validation in test environment
        if os.getenv("TESTING") == "true":
            return v
        if not v:
            raise ValueError("OpenAI API key is required")
        return v
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings() 