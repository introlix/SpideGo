import hashlib
from backend.utils.web_crawler import web_crawler, ScrapeResult
from backend.utils.text_chunker import TextChunker
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP_SIZE, TOTAL_CHUNK_CAP
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

        chunker = TextChunker(chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP_SIZE)
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
            }
            relevant_chunks.append(chunk_record)

        final_chunks = []
        current = None

        for r_chunk in relevant_chunks:
            if current is None:
                current = r_chunk.copy()
                continue

            if len(current['chunk_text'] + r_chunk['chunk_text']) <= TOTAL_CHUNK_CAP:
                current['chunk_text'] += "\n\n" + r_chunk['chunk_text']
                current['score'] = max(current['score'], r_chunk['score'])
            else:
                final_chunks.append(current)
                current = r_chunk.copy()

        if current:
            final_chunks.append(current)
            

        final_chunks.sort(key=lambda x: x["score"], reverse=True)

        # Pick the highest-scoring final chunk (as a dict) and split it into sentences
        if not final_chunks:
            return []

        top_chunk = final_chunks[:1]
        final_chunk_result = []

        try:
            top_chunk_text = top_chunk[0].get("chunk_text", "")

            final_chunk_sentences = chunker.split_by_sentences(top_chunk_text)

            if not final_chunk_sentences:
                return []

            final_chunk_sentences_emb = embedding_model.encode(final_chunk_sentences, batch_size=32)
            final_similarities = embedding_model.similarity(query_embedding, final_chunk_sentences_emb)[0]

            for idx, sentence in enumerate(final_chunk_sentences):
                final_similarity_score = float(final_similarities[idx])
                if final_similarity_score < similarity_threshold:
                    print(f"skiping this with score: {final_similarity_score} and sentence: {sentence}")
                    continue

                final_chunk_result.append(sentence)
        except Exception as e:
            print(f"Error While filtering wanted chunk : {e}")

        if top_chunk:
            top_chunk[0]['chunk_text'] = " ".join(final_chunk_result)

        return top_chunk
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []
