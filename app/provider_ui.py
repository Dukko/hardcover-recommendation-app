from app.providers import (
    get_available_anthropic_models,
    get_available_gemini_models,
    get_available_openai_models,
    get_available_openrouter_models,
)
from app.session import Credentials

PROVIDER_KEY_ATTR = {
    "Gemini": "gemini_key",
    "OpenAI": "openai_key",
    "Anthropic": "anthropic_key",
    "OpenRouter": "openrouter_key",
}


def list_available_providers(creds: Credentials) -> list[str]:
    return [name for name, attr in PROVIDER_KEY_ATTR.items() if getattr(creds, attr)]


async def fetch_models_for_provider(provider: str, creds: Credentials) -> list[str]:
    if provider == "Gemini":
        return await get_available_gemini_models(creds.gemini_key)
    if provider == "OpenAI":
        return await get_available_openai_models(creds.openai_key)
    if provider == "Anthropic":
        return await get_available_anthropic_models(creds.anthropic_key)
    if provider == "OpenRouter":
        return await get_available_openrouter_models(creds.openrouter_key)
    return []


def default_model_index(provider: str, models: list[str]) -> int:
    if provider == "Gemini":
        needle = ("flash", "1.5")
    elif provider == "OpenAI":
        needle = ("gpt-4o",)
    elif provider == "Anthropic":
        needle = ("sonnet", "3-5")
    else:
        return 0

    for i, m in enumerate(models):
        low = m.lower()
        if all(n in low for n in needle) and not (provider == "OpenAI" and "mini" in low):
            return i
    return 0


async def build_settings_context(creds: Credentials) -> dict:
    providers = list_available_providers(creds)
    selected_provider = providers[0] if providers else None
    models: list[str] = []
    default_ix = 0
    if selected_provider:
        models = await fetch_models_for_provider(selected_provider, creds)
        default_ix = default_model_index(selected_provider, models)

    return {
        "creds": creds,
        "available_providers": providers,
        "selected_provider": selected_provider,
        "models": models,
        "default_model_index": default_ix,
    }
