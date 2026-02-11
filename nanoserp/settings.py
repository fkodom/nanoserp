from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: str | None = None

    class Config:
        env_prefix = "NANOSERP_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
