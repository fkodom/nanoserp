from pydantic import Field
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    API_KEY: str | None = None

    class Config:
        env_prefix = "{{REPO_NAME_ALLCAPS}}_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    URL: str
    MAX_CONNECTIONS: int = Field(default=32, ge=1, le=256)

    class Config:
        env_prefix = "{{REPO_NAME_ALLCAPS}}_DATABASE_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
