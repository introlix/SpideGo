import requests
from fastapi import APIRouter

router = APIRouter(prefix="/search/suggestions", tags=["search"])

@router.get("/")
async def search_suggestions(query: str):
    url = "https://duckduckgo.com/ac/"
    params = {
        "q": query,
        "kl": "us-en",
    }

    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()

    return [item["phrase"] for item in response.json()]