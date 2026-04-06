from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT = "change-me-in-production-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/million_miles"

    # JWT
    secret_key: str = _INSECURE_DEFAULT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # App
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

if settings.secret_key == _INSECURE_DEFAULT and not settings.debug:
    raise RuntimeError(
        "SECRET_KEY is not set. "
        "Generate one with: openssl rand -hex 32  "
        "and add it to your .env file."
    )
