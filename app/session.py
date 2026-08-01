from dataclasses import dataclass

from starlette.requests import Request

from app.config import settings


@dataclass
class Credentials:
    hardcover_token: str
    gemini_key: str
    openai_key: str
    anthropic_key: str


def get_credentials(request: Request) -> Credentials:
    """Browser-entered overrides (session cookie) win; otherwise fall back to env vars."""
    overrides = request.session.get("credentials", {})
    return Credentials(
        hardcover_token=overrides.get("hardcover_token") or settings.hardcover_token,
        gemini_key=overrides.get("gemini_key") or settings.gemini_key,
        openai_key=overrides.get("openai_key") or settings.openai_key,
        anthropic_key=overrides.get("anthropic_key") or settings.anthropic_key,
    )


def set_credentials(request: Request, credentials: Credentials) -> None:
    request.session["credentials"] = {
        "hardcover_token": credentials.hardcover_token,
        "gemini_key": credentials.gemini_key,
        "openai_key": credentials.openai_key,
        "anthropic_key": credentials.anthropic_key,
    }


def bearer_token(hardcover_token: str) -> str:
    if hardcover_token and not hardcover_token.startswith("Bearer "):
        return f"Bearer {hardcover_token}"
    return hardcover_token
