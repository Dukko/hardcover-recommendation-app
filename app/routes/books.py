import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.hardcover_client import search_books_suggestions
from app.session import bearer_token, get_credentials
from app.templating import templates

router = APIRouter()


def _extract_author(doc: dict) -> str:
    """Hardcover's search document shape for author isn't in our own schema (it's their
    search index), so try the field names most likely to be present and fall back to
    blank rather than guessing wrong."""
    for key in ("author_names", "authors"):
        value = doc.get(key)
        if isinstance(value, list) and value:
            names = [v if isinstance(v, str) else v.get("name", "") for v in value]
            names = [n for n in names if n]
            if names:
                return ", ".join(names[:2])

    contributions = doc.get("contributions")
    if isinstance(contributions, list):
        names = [c["author"]["name"] for c in contributions if c.get("author") and c["author"].get("name")]
        if names:
            return ", ".join(names[:2])

    author_name = doc.get("author_name")
    if isinstance(author_name, str) and author_name:
        return author_name

    return ""


@router.get("/books/search", response_class=HTMLResponse)
async def books_search(request: Request, q: str = ""):
    q = q.strip()
    creds = get_credentials(request)

    if len(q) < 2 or not creds.hardcover_token:
        return templates.TemplateResponse(request, "partials/autocomplete_results.html", {"suggestions": []})

    token = bearer_token(creds.hardcover_token)
    async with httpx.AsyncClient() as client:
        docs = await search_books_suggestions(client, token, q)

    suggestions = [
        {"title": doc.get("title", ""), "author": _extract_author(doc)}
        for doc in docs
        if doc.get("title")
    ]
    return templates.TemplateResponse(request, "partials/autocomplete_results.html", {"suggestions": suggestions})
