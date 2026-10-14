import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Server configuration
    PORT: int = Field(default=4000, validation_alias="PORT")
    HOST: str = Field(default="0.0.0.0", validation_alias="HOST")
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    CLIENT_ORIGIN: str = Field(default="http://localhost:5173", validation_alias="CLIENT_ORIGIN")

    # MongoDB configuration
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", validation_alias="MONGODB_URL")
    MONGODB_DB_NAME: str = Field(default="agentqa", validation_alias="MONGODB_DB_NAME")
    MONGODB_CONNECT_TIMEOUT_MS: int = Field(default=2000, validation_alias="MONGODB_CONNECT_TIMEOUT_MS")

    # Security & Tokens
    JWT_SECRET: str = Field(default="agentqa_super_secure_jwt_secret_dev_key_2026", validation_alias="JWT_SECRET")
    JWT_EXPIRES_IN_SECONDS: int = Field(default=15 * 60, validation_alias="JWT_EXPIRES_IN_SECONDS")  # 15 minutes
    JWT_REMEMBER_EXPIRES_IN_SECONDS: int = Field(default=30 * 24 * 60 * 60, validation_alias="JWT_REMEMBER_EXPIRES_IN_SECONDS")  # 30 days
    RESET_TOKEN_EXPIRES_IN_SECONDS: int = Field(default=15 * 60, validation_alias="RESET_TOKEN_EXPIRES_IN_SECONDS")  # 15 minutes

    # Security & SSRF
    ALLOW_LOCAL_TEST_TARGETS: bool = Field(default=False, validation_alias="ALLOW_LOCAL_TEST_TARGETS")

    # Default Seed Admin Account
    DEFAULT_ADMIN_EMAIL: str = Field(default="admin@example.com", validation_alias="DEFAULT_ADMIN_EMAIL")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="Admin@123", validation_alias="DEFAULT_ADMIN_PASSWORD")
    DEFAULT_ADMIN_NAME: str = Field(default="System Administrator", validation_alias="DEFAULT_ADMIN_NAME")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
