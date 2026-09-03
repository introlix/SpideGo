import httpx
from backend.config import SEARXNG_URL

headers = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

async def search(query: str, tab: str):
    params = {
        "q": query,
        "format": "json",
        "language": "auto",
        "time_range": "",
        "safesearch": 0,
        "categories": tab
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(SEARXNG_URL, params=params, headers=headers, timeout=5.0)
        response.raise_for_status()

    return response.json()