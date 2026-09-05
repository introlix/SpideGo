import asyncio
import tldextract
from fastapi import APIRouter
from backend.config import MAX_CONCURRENT_URLS
from backend.utils.caching import (
    get_cached_feature_snippets,
    save_feature_snippets
)
from backend.services.featured_snippets import crawl_and_chunk, get_wikipedia_summary

router = APIRouter(prefix="/search/featured_snippets", tags=["search"])


@router.post("/")
async def featured_snippets(query: str, urls: list[str]):
    if get_cached_feature_snippets(query):
        return get_cached_feature_snippets(query)

    crawl_tasks = []
    url_semaphore = asyncio.Semaphore(MAX_CONCURRENT_URLS)

    async def crawl_with_limit(url):
        async with url_semaphore:
            return await crawl_and_chunk(query, url)

    flat_records = []
    for url in urls:
        if isinstance(url, Exception):
            print(f"Error checking URL existence: {url}")
            continue
        if url:
            ext = tldextract.extract(url)
            core_name = ext.domain

            if core_name == "wikipedia":
                result = await get_wikipedia_summary(query, url)
                flat_records.extend(result)
                continue

            crawl_tasks.append(crawl_with_limit(url))

    if not crawl_tasks:
        return []

    for task in asyncio.as_completed(crawl_tasks):
        try:
            rec_list = await task
        except Exception as e:
            continue

        if isinstance(rec_list, list) and rec_list:
            flat_records.extend(rec_list)
        elif isinstance(rec_list, Exception):
            print(f"Error during crawling: {rec_list}")

    flat_records.sort(key=lambda x: x['score'], reverse=True)

    save_feature_snippets(query, flat_records)

    return flat_records
