import asyncio
import json
import time

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from app.hardcover_client import fetch_enhanced_library
from app.providers import get_provider
from app.recommend import get_ai_recommendations, parse_recommendations, verify_and_enrich
from app.session import bearer_token, get_credentials
from app.sse import sse_event
from app.templating import templates

router = APIRouter()


@router.get("/recommend/start", response_class=HTMLResponse)
async def recommend_start(request: Request):
    return templates.TemplateResponse(
        request, "partials/recommend_panel.html", {"query_string": request.url.query}
    )


@router.get("/recommend/stream")
async def recommend_stream(
    request: Request,
    provider: str,
    model: str = "",
    moods: str = "",
    genres: str = "",
    pages: int = 400,
    min_rating: float = 3.0,
    year_start: int = 1897,
    year_end: int = 2026,
    skew_books: list[str] = Query(default=[]),
):
    creds = get_credentials(request)

    def render_error(message: str) -> str:
        return templates.get_template("partials/error.html").render(message=message)

    async def event_generator():
        try:
            if not creds.hardcover_token:
                yield sse_event("error", render_error("Missing Hardcover token. Add it in Settings."))
                yield sse_event("done", "")
                return

            api_keys = {"Gemini": creds.gemini_key, "OpenAI": creds.openai_key, "Anthropic": creds.anthropic_key}
            if not api_keys.get(provider):
                yield sse_event("error", render_error(f"No API key configured for {provider}."))
                yield sse_event("done", "")
                return

            yield sse_event("progress", "<p>📥 Fetching your library from Hardcover...</p>")
            token = bearer_token(creds.hardcover_token)
            library, error = await fetch_enhanced_library(token)
            if error:
                yield sse_event("error", render_error(error))
                yield sse_event("done", "")
                return

            yield sse_event("progress", f"<p>🧠 Analyzing {len(library)} books for patterns...</p>")
            filters = {
                "moods": moods,
                "genres": genres,
                "pages": pages,
                "year_range": (year_start, year_end),
                "min_rating": min_rating,
                "skew_books": [b.strip() for b in skew_books if b.strip()][:3],
            }

            try:
                ai_provider = get_provider(provider, api_keys[provider], model)
                task = asyncio.ensure_future(get_ai_recommendations(ai_provider, library, filters))
                start = time.monotonic()
                while not task.done():
                    await asyncio.wait({task}, timeout=3)
                    if not task.done():
                        elapsed = int(time.monotonic() - start)
                        yield sse_event(
                            "progress", f"<p>🧠 Still thinking... ({elapsed}s elapsed, {len(library)} books analyzed)</p>"
                        )
                recs_text, used_model = task.result()
                if not recs_text:
                    raise ValueError("No response from AI provider.")
            except Exception as e:
                yield sse_event("error", render_error(f"Error calling {provider}: {str(e)}"))
                yield sse_event("done", "")
                return

            yield sse_event("progress", "<p>🔍 Verifying books in Hardcover database...</p>")
            try:
                recommendations = parse_recommendations(recs_text)
            except json.JSONDecodeError:
                html = templates.get_template("partials/raw_response.html").render(raw_text=recs_text)
                yield sse_event("error", html)
                yield sse_event("done", "")
                return

            results = await verify_and_enrich(token, recommendations)

            yield sse_event("progress", "<p>✅ Complete!</p>")
            html = templates.get_template("partials/results.html").render(
                results=results, used_model=used_model, book_count=len(library)
            )
            yield sse_event("result", html)
            yield sse_event("done", "")
        except Exception as e:
            yield sse_event("error", render_error(str(e)))
            yield sse_event("done", "")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
