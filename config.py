"""
Centralized application configuration.

WHY THIS FILE EXISTS:
Every value that changes between environments (local dev, Docker, CI,
"production") lives here and is read from environment variables — never
hardcoded in business logic. This is what lets the SAME code run against
a local Postgres, a Dockerized Postgres, or a managed cloud Postgres,
just by changing environment variables (12-factor app principle).

INTERVIEW ANSWER: "How is configuration managed?"
-> "Pydantic Settings loads env vars once at startup into a typed,
   validated object. Nothing reads os.environ directly elsewhere."
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://bizsync_user:bizsync_pass@localhost:5432/bizsync"

    # Auth
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8  # 8-hour session

    # App
    APP_NAME: str = "BizSync API"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
