import asyncio
import json
import re

import httpx

from app.hardcover_client import search_hardcover_books

RECENT_READS_LIMIT = 60
MAX_CONCURRENT_VERIFICATIONS = 5


def build_prompt(library: list[dict], filters: dict) -> str:
    titles_read = [b["title"] for b in library]
    recent_reads = "\n".join(
        f"- {b['full_str']} (My Rating: {b['rating']}/5, Tags: {b['tags']})" for b in library[:RECENT_READS_LIMIT]
    )
    start_year, end_year = filters["year_range"]
    skew_books = filters.get("skew_books") or []
    skew_section = ""
    if skew_books:
        skew_list = "\n".join(f"- {title}" for title in skew_books)
        skew_section = f"""
    **SKEW TOWARD THESE BOOKS:**
    Strongly favor recommendations with a similar vibe, themes, or writing style to:
    {skew_list}
"""

    return f"""
    Act as an elite literary curator.

    **USER REQUEST:**
    Recommend 10 books matching these strict criteria:
    - **Moods:** {filters['moods']}
    - **Genres:** {filters['genres']}
    - **Length:** ~{filters['pages']} pages
    - **Publication Year:** Must be published between {start_year} and {end_year}
    - **Min Rating:** Must have a rating of {filters['min_rating']} or higher
{skew_section}
    **EXCLUSION LIST:**
    {titles_read}

    **USER TASTE PROFILE (Based on recent reads):**
    {recent_reads}

    **OUTPUT FORMAT (JSON Array):**
    Return ONLY a valid JSON array with no markdown, no code blocks. Example:
    [
      {{"title": "Book Title", "author": "Author Name", "reason": "Why it fits"}},
      {{"title": "Another Book", "author": "Another Author", "reason": "Why it fits"}}
    ]
    """


async def get_ai_recommendations(provider, library: list[dict], filters: dict) -> tuple[str, str]:
    prompt = build_prompt(library, filters)
    return await asyncio.to_thread(provider.get_recommendations, prompt)


def parse_recommendations(recs_text: str) -> list[dict]:
    json_match = re.search(r"```json\n(.*)\n```", recs_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        array_match = re.search(r"\[.*\]", recs_text, re.DOTALL)
        json_str = array_match.group(0).strip() if array_match else recs_text.strip()
    return json.loads(json_str)


async def verify_and_enrich(hc_token: str, recommendations: list[dict], limit: int = 10) -> list[dict]:
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_VERIFICATIONS)
    results: list[dict] = []

    async with httpx.AsyncClient() as client:

        async def verify_one(rec: dict) -> dict | None:
            async with semaphore:
                try:
                    return await search_hardcover_books(client, hc_token, rec.get("title", ""), rec.get("author", ""))
                except Exception:
                    return None

        book_data_list = await asyncio.gather(*(verify_one(rec) for rec in recommendations))

        for rec, book_data in zip(recommendations, book_data_list):
            if len(results) >= limit:
                break
            if not book_data or book_data.get("ratings_count", 0) < 3:
                continue

            moods_data = book_data.get("moods", [])
            genres_data = book_data.get("genres", [])
            rating = book_data.get("rating", "N/A")
            if isinstance(rating, (int, float)):
                rating = round(rating, 1)

            book_slug = book_data.get("slug", "")
            hardcover_link = f"https://hardcover.app/books/{book_slug}" if book_slug else "#"

            results.append(
                {
                    "title": book_data.get("title", rec.get("title")),
                    "author": rec.get("author", ""),
                    "rating": rating,
                    "moods": moods_data[:3],
                    "genres": genres_data[:3],
                    "reason": rec.get("reason", ""),
                    "link": hardcover_link,
                }
            )

    return results
