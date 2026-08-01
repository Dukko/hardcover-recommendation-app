import httpx

from app.cache import library_cache, search_cache

HARDCOVER_URL = "https://api.hardcover.app/v1/graphql"
SEARCH_RESULTS_LIMIT = 5

LIBRARY_QUERY = """
query GetEnhancedLibrary {
  me {
    user_books(
      where: { status_id: { _eq: 3 } }
      limit: 1000
      order_by: { updated_at: desc }
    ) {
      rating
      book {
        title
        release_date
        rating
        taggings(limit: 5) { tag { tag } }
        contributions { author { name } }
      }
    }
  }
}
"""


async def fetch_enhanced_library(token: str) -> tuple[list[dict] | None, str | None]:
    async def factory():
        return await _fetch_enhanced_library(token)

    return await library_cache.aget_or_set(token, factory)


async def _fetch_enhanced_library(token: str) -> tuple[list[dict] | None, str | None]:
    headers = {"authorization": token, "content-type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(HARDCOVER_URL, json={"query": LIBRARY_QUERY}, headers=headers)
        if response.status_code != 200:
            return None, f"HTTP Error {response.status_code}"

        data = response.json()
        if "errors" in data:
            return None, f"GraphQL Error: {data['errors'][0]['message']}"

        return parse_library_response(data), None
    except Exception as e:
        return None, str(e)


def parse_library_response(data: dict) -> list[dict]:
    raw_books = data.get("data", {}).get("me", [])[0].get("user_books", [])
    library = []
    for entry in raw_books:
        try:
            book = entry.get("book", {})
            authors = [
                c["author"]["name"]
                for c in book.get("contributions", [])
                if c.get("author") and c["author"].get("name")
            ]
            author_str = ", ".join(authors) if authors else "Unknown"
            r_date = book.get("release_date", "")
            year = r_date[:4] if r_date else "Unknown"
            community_rating = book.get("rating")
            tags = [t["tag"]["tag"] for t in book.get("taggings", []) if t.get("tag")]
            tags_str = ", ".join(tags) if tags else "Untagged"

            library.append(
                {
                    "title": book.get("title", "Unknown"),
                    "author": author_str,
                    "rating": entry.get("rating", 0),
                    "year": year,
                    "community_rating": community_rating,
                    "tags": tags_str,
                    "full_str": f"{book.get('title')} by {author_str} ({year})",
                }
            )
        except Exception:
            continue
    return library


async def _search_raw(client: httpx.AsyncClient, token: str, query_text: str, per_page: int) -> list[dict]:
    headers = {"authorization": token, "content-type": "application/json"}
    query_escaped = query_text.replace('"', '\\"')

    query = f"""
    query SearchBooks {{
      search(
        query: "{query_escaped}"
        query_type: "Book"
        per_page: {per_page}
        page: 1
      ) {{
        results
      }}
    }}
    """

    try:
        response = await client.post(HARDCOVER_URL, json={"query": query}, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()
        if "errors" in data:
            return []

        hits = data.get("data", {}).get("search", {}).get("results", {}).get("hits", [])
        return [hit.get("document", {}) for hit in hits if hit.get("document")]
    except Exception:
        return []


async def search_hardcover_books(client: httpx.AsyncClient, token: str, title: str, author: str | None = None) -> dict | None:
    async def factory():
        hits = await _search_raw(client, token, title, SEARCH_RESULTS_LIMIT)
        return hits[0] if hits else None

    return await search_cache.aget_or_set((token, title, author), factory)


async def search_books_suggestions(client: httpx.AsyncClient, token: str, query_text: str, limit: int = 6) -> list[dict]:
    async def factory():
        return await _search_raw(client, token, query_text, limit)

    return await search_cache.aget_or_set((token, "suggest", query_text, limit), factory)
