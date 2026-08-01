import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Env vars are matched case-insensitively, e.g. HARDCOVER_TOKEN -> hardcover_token."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hardcover_token: str = ""
    gemini_key: str = ""
    openai_key: str = ""
    anthropic_key: str = ""
    # Signs the session cookie that holds browser-entered key overrides. Set this
    # explicitly (env var SESSION_SECRET) if you want those overrides to survive a
    # container restart -- otherwise a new random secret is generated every boot.
    session_secret: str = ""


settings = Settings()
if not settings.session_secret:
    settings.session_secret = secrets.token_hex(32)
