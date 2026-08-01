from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.config import settings
from app.routes import books, models, pages, recommend

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Hardcover AI Librarian")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(pages.router)
app.include_router(models.router)
app.include_router(recommend.router)
app.include_router(books.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
