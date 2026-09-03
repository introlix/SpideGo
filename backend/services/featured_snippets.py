import hashlib
from backend.services.web_crawler import web_crawler, ScrapeResult
from backend.services.text_chunker import TextChunker
from backend.config import CHUNK_SIZE, TOTAL_CHUNK_CAP
from backend.utils.embedding_model_state import embeddingmodelstate
from backend.utils.caching import (
    get_cached_page,
    save_page,
)


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

        chunker = TextChunker(chunk_size=CHUNK_SIZE)
        chunks = chunker.chunk_text(page_text)

        chunk_texts = [chunk["text"] for chunk in chunks]

        # There is many empty chunks
        if not chunk_texts:
            return []

        embedding_model = embeddingmodelstate.get_model()

        query_prefix = "Represent this sentence for searching relevant passages: "
        query_embedding = embedding_model.encode([f"{query_prefix}{query}"])
        chunk_embeddings = embedding_model.encode(chunk_texts, batch_size=32)

        similarities = embedding_model.similarity(query_embedding, chunk_embeddings)[0]

        relevant_chunks = []
        similarity_threshold = 0.60

        for idx, chunk in enumerate(chunks):
            similarity_score = float(similarities[idx])

            if similarity_score < similarity_threshold:
                continue

            chunk_record = {
                "_id": f"{hashlib.md5(url.encode()).hexdigest()}_chunk_{chunk['chunk_id']}",
                "title": page_title,
                "description": page_description,
                "url": page_url,
                "chunk_id": chunk["chunk_id"],
                "chunk_text": chunk["text"],
                "score": similarity_score,
                "token_count": chunk.get(
                    "token_count", chunker.count_tokens(chunk["text"])
                ),
            }
            relevant_chunks.append(chunk_record)

        final_chunks = []
        seen_sentences = set()
        used_tokens = 0

        relevant_chunks.sort(key=lambda x: x["score"], reverse=True)

        seen = set()
        unique_relevant_chunks = []
        for chunk in relevant_chunks:
            if chunk["chunk_text"] not in seen:
                unique_relevant_chunks.append(chunk)
                seen.add(chunk["chunk_text"])

        relevant_chunks = unique_relevant_chunks

        for relevant_chunk in relevant_chunks:
            chunk_tokens = relevant_chunk.get(
                "token_count", chunker.count_tokens(relevant_chunk["chunk_text"])
            )
            separator_tokens = chunker.count_tokens("\n\n") if final_chunks else 0

            if used_tokens + separator_tokens + chunk_tokens <= TOTAL_CHUNK_CAP:
                # See if the first sentence of the current chunk is good or not. If its good then append it if not then remove that sentence and check again till get best and then append it.
                relevant_sentences = chunker.split_by_sentences(
                    relevant_chunk["chunk_text"]
                )

                kept_sentences = []
                found_good_start = False

                for sentence in relevant_sentences:
                    sentence_key = " ".join(sentence.split())

                    if sentence_key in seen_sentences:
                        continue

                    if not found_good_start:
                        sentence_embedding = embedding_model.encode(
                            [sentence], batch_size=32
                        )

                        sentence_similarity = embedding_model.similarity(
                            query_embedding, sentence_embedding
                        )[0][0]

                        if sentence_similarity >= 0.45:
                            found_good_start = True
                        else:
                            continue

                    kept_sentences.append(sentence)
                    seen_sentences.add(sentence_key)

                relevant_chunk["chunk_text"] = "\n\n".join(kept_sentences)

                chunk_tokens = chunker.count_tokens(relevant_chunk["chunk_text"])

                final_chunks.append(relevant_chunk)
                used_tokens += separator_tokens + chunk_tokens

        if not final_chunks and relevant_chunks:
            final_chunks.append(relevant_chunks[0])

        final_chunks.sort(key=lambda x: x["chunk_id"])

        final_text = "\n\n".join(chunk["chunk_text"] for chunk in final_chunks)

        final_chunk = [
            {
                **final_chunks[0],
                "chunk_text": final_text,
                "score": max(chunk["score"] for chunk in final_chunks),
            }
        ]

        # Pick the highest-scoring final chunk (as a dict) and split it into sentences
        if not final_chunk:
            return []

        return final_chunk
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []
