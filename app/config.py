from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Job Tracker API"
    debug: bool = False
    database_url: str
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    @field_validator("database_url")
    @classmethod
    def normalise_database_url(cls, v: str) -> str:
        # Railway supplies postgres:// — SQLAlchemy 2.x requires postgresql://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v


settings = Settings()
