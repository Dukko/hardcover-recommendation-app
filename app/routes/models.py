from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.provider_ui import default_model_index, fetch_models_for_provider
from app.session import get_credentials
from app.templating import templates

router = APIRouter()


@router.get("/models", response_class=HTMLResponse)
async def models_fragment(request: Request, provider: str):
    creds = get_credentials(request)
    models = await fetch_models_for_provider(provider, creds)
    default_ix = default_model_index(provider, models)
    return templates.TemplateResponse(
        request,
        "partials/model_select.html",
        {"models": models, "default_model_index": default_ix, "selected_provider": provider},
    )
