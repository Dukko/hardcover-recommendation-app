import asyncio

from anthropic import Anthropic
from google import genai
from openai import OpenAI

from app.cache import model_cache

# --- AI PROVIDERS ---


class GeminiProvider:
    def __init__(self, api_key: str, model_name: str):
        clean_name = model_name or "gemini-flash-latest"
        if "/" not in clean_name:
            clean_name = f"models/{clean_name}"
        self.model_name = clean_name
        self.client = genai.Client(api_key=api_key)

    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            return response.text, self.model_name
        except Exception as e:
            raise Exception(f"Gemini API error ({self.model_name}): {str(e)}") from e


class OpenAIProvider:
    def __init__(self, api_key: str, model_name: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name or "gpt-4o-mini"

    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an elite literary curator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content, self.model_name
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e


class AnthropicProvider:
    def __init__(self, api_key: str, model_name: str):
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name or "claude-3-5-sonnet-20241022"

    def get_recommendations(self, prompt: str) -> tuple[str, str]:
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text, self.model_name
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}") from e


def get_provider(provider_name: str, api_key: str, specific_model: str | None = None):
    if provider_name == "Gemini":
        return GeminiProvider(api_key, specific_model)
    elif provider_name == "OpenAI":
        return OpenAIProvider(api_key, specific_model)
    elif provider_name == "Anthropic":
        return AnthropicProvider(api_key, specific_model)
    raise ValueError("Invalid provider selected")


# --- MODEL LISTS (cached, run blocking SDK calls off the event loop) ---


async def get_available_gemini_models(api_key: str) -> list[str]:
    # Hardcoded to the current latest stable Flash version, same as before.
    return ["gemini-flash-latest"]


async def get_available_openai_models(api_key: str) -> list[str]:
    async def factory():
        return await asyncio.to_thread(_fetch_openai_models, api_key)

    return await model_cache.aget_or_set(("openai", api_key), factory)


def _fetch_openai_models(api_key: str) -> list[str]:
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        valid_models = [
            m.id
            for m in models.data
            if "gpt" in m.id.lower()
            and not any(x in m.id.lower() for x in ["instruct", "realtime", "audio", "voice"])
        ]
        valid_models.sort(reverse=True)
        return valid_models
    except Exception:
        return []


async def get_available_anthropic_models(api_key: str) -> list[str]:
    async def factory():
        return await asyncio.to_thread(_fetch_anthropic_models, api_key)

    return await model_cache.aget_or_set(("anthropic", api_key), factory)


def _fetch_anthropic_models(api_key: str) -> list[str]:
    try:
        client = Anthropic(api_key=api_key)
        page = client.models.list(limit=20)
        valid_models = [m.id for m in page.data if "claude" in m.id.lower() and "instant" not in m.id.lower()]
        valid_models.sort(reverse=True)
        return valid_models
    except Exception:
        return ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]
