from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app.provider_ui import build_settings_context
from app.session import Credentials, get_credentials, set_credentials
from app.templating import templates

router = APIRouter()

DEFAULT_FILTERS = {
    "moods": "Eerie, Dark",
    "genres": "Gothic Horror, Horror",
    "pages": 400,
    "min_rating": 3.0,
    "year_start": 1897,
}


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    creds = get_credentials(request)
    context = await build_settings_context(creds)
    context.update(
        request=request,
        current_year=datetime.now().year,
        filters=DEFAULT_FILTERS,
    )
    return templates.TemplateResponse(request, "index.html", context)


@router.post("/credentials", response_class=HTMLResponse)
async def save_credentials(
    request: Request,
    hardcover_token: str = Form(""),
    gemini_key: str = Form(""),
    openai_key: str = Form(""),
    anthropic_key: str = Form(""),
    openrouter_key: str = Form(""),
):
    creds = Credentials(
        hardcover_token=hardcover_token.strip(),
        gemini_key=gemini_key.strip(),
        openai_key=openai_key.strip(),
        anthropic_key=anthropic_key.strip(),
        openrouter_key=openrouter_key.strip(),
    )
    set_credentials(request, creds)
    context = await build_settings_context(creds)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/settings_panel.html", context)
