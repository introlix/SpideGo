import asyncio
import hashlib
from fastapi import APIRouter
from backend.utils.web_crawler import web_crawler, ScrapeResult
from backend.utils.text_chunker import TextChunker
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP_SIZE, MAX_CONCURRENT_URLS
from backend.utils.embedding_model_state import embeddingmodelstate
from backend.utils.caching import (
    get_cached_feature_snippets,
    get_cached_page,
    save_feature_snippets,
    save_page,
)

router = APIRouter(prefix="/search/featured_snippets", tags=["search"])


async def crawl_and_chunk(query: str, url: str) -> list:
    try:
        crawled_result = get_cached_page(url)

        if not crawled_result:
            crawled_result = await web_crawler(url=url)
            if isinstance(crawled_result, ScrapeResult):
                to_save = {
                    "text": crawled_result.text,
                    "title": crawled_result.title,
                    "description": crawled_result.description,
                    "url": crawled_result.url,
                }
            else:
                to_save = crawled_result
            save_page(url, to_save)

        if isinstance(crawled_result, ScrapeResult):
            page_text = crawled_result.text or ""
            page_title = crawled_result.title or ""
            page_description = crawled_result.description or ""
            page_url = crawled_result.url or url
        elif isinstance(crawled_result, dict):
            page_text = crawled_result.get("text", "") or ""
            page_title = crawled_result.get("title", "") or ""
            page_description = crawled_result.get("description", "") or ""
            page_url = crawled_result.get("url", url) or url
        elif isinstance(crawled_result, str):
            page_text = crawled_result
            page_title = ""
            page_description = ""
            page_url = url
        else:
            return []

        if not isinstance(page_text, str) or not page_text.strip():
            return []

        chunker = TextChunker(chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP_SIZE)
        chunks = chunker.chunk_text(page_text)

        chunk_texts = [chunk["text"] for chunk in chunks]

        # There is many empty chunks
        if not chunk_texts:
            return []

        embedding_model = embeddingmodelstate.get_model()

        query_embedding = embedding_model.encode_query(query)
        chunk_embeddings = embedding_model.encode_document(chunk_texts, batch_size=32)

        similarities = embedding_model.similarity(query_embedding, chunk_embeddings)[0]

        relevant_chunks = []
        similarity_threshold = 0.40
        seen_page_urls = set()

        for idx, chunk in enumerate(chunks):
            similarity_score = float(similarities[idx])

            if similarity_score < similarity_threshold:
                continue
            if page_url in seen_page_urls:
                continue

            seen_page_urls.add(page_url)

            chunk_record = {
                "_id": f"{hashlib.md5(url.encode()).hexdigest()}_chunk_{chunk['chunk_id']}",
                "title": page_title,
                "description": page_description,
                "url": page_url,
                "chunk_id": chunk["chunk_id"],
                "chunk_text": chunk["text"],
            }
            relevant_chunks.append(chunk_record)

        return relevant_chunks
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []


@router.post("/")
async def featured_snippets(query: str, urls: list[str]):
    if get_cached_feature_snippets(query):
        return get_cached_feature_snippets(query)

    crawl_tasks = []
    url_semaphore = asyncio.Semaphore(MAX_CONCURRENT_URLS)

    async def crawl_with_limit(url):
        async with url_semaphore:
            return await crawl_and_chunk(query, url)

    for url in urls:
        if isinstance(url, Exception):
            print(f"Error checking URL existence: {url}")
            continue
        if url:
            crawl_tasks.append(crawl_with_limit(url))

    if not crawl_tasks:
        return []

    flat_records = []
    for task in asyncio.as_completed(crawl_tasks):
        try:
            rec_list = await task
        except Exception as e:
            continue

        if isinstance(rec_list, list) and rec_list:
            flat_records.extend(rec_list)
        elif isinstance(rec_list, Exception):
            print(f"Error during crawling: {rec_list}")

    save_feature_snippets(query, flat_records)

    return flat_records
