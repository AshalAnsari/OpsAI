from pathlib import Path

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Harbor Dock Station API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    debug: bool = True

    database_url: str = "mysql+pymysql://harbordock:harbordock@localhost:3306/harbordock"

    jwt_secret_key: str = "change-me-in-production-harbordock-demo-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

    stripe_secret_key: str = "sk_test_placeholder"
    stripe_publishable_key: str = "pk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_currency: str = "usd"

    seed_admin_email: str = "admin@harbordock.demo"
    seed_admin_password: str = "AdminDemo123!"
    seed_customer_password: str = "CustomerDemo123!"

    # Optional SMTP for support reply emails (empty host = demo/log only)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@harbordock.demo"
    smtp_use_tls: bool = True

    fulfillment_cron_enabled: bool = True
    # Override interval in minutes. When unset: 10 in development, 60 in production.
    fulfillment_advance_interval_minutes: int | None = None

    # AI OS (LangGraph) — prefer OpenRouter like AI Roadmap notebooks
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_api_key: str = ""
    ai_model: str = "openai/gpt-4o-mini"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def fulfillment_interval_minutes(self) -> int:
        if self.fulfillment_advance_interval_minutes is not None:
            return max(1, self.fulfillment_advance_interval_minutes)
        if self.app_env.lower() in {"production", "prod"}:
            return 60
        return 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
