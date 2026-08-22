import random
import requests

SEARXNG_URL = "http://localhost:8888/search"  # your local instance

RELIABLE = ["duckduckgo"]
ROTATING_POOL = ["brave", "startpage", "google", "qwant"]

def pick_engines():
    return RELIABLE + [random.choice(ROTATING_POOL)]

def search(query: str):
    engines = pick_engines()
    params = {
        "q": query,
        "format": "json",
        "engines": ",".join(engines),
        "language": "auto",
        "time_range": "",
        "safesearch": 0,
        "theme": "simple"
    }
    response = requests.get(SEARXNG_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

# usage
results = search("robot perception SLAM")
for r in results["results"]:
    print(r["title"], "-", r["url"])