import numpy as np
from fastembed import TextEmbedding


class EmbeddingModelState:
    def __init__(self):
        self.embedding = None

    def load_embedding(self):
        self.embedding = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return self.embedding

    def get_model(self):
        if self.embedding is None:
            self.load_embedding()
        return self

    def encode(self, texts, batch_size=None):
        if self.embedding is None:
            self.load_embedding()

        if isinstance(texts, str):
            texts = [texts]

        vectors = list(self.embedding.embed(texts))
        return np.asarray(vectors, dtype=np.float32)

    def similarity(self, query_embedding, candidate_embeddings):
        query_vectors = np.asarray(query_embedding, dtype=np.float32)
        candidate_vectors = np.asarray(candidate_embeddings, dtype=np.float32)

        if query_vectors.ndim == 1:
            query_vectors = query_vectors.reshape(1, -1)
        if candidate_vectors.ndim == 1:
            candidate_vectors = candidate_vectors.reshape(1, -1)

        if query_vectors.size == 0 or candidate_vectors.size == 0:
            return np.zeros((query_vectors.shape[0], candidate_vectors.shape[0]), dtype=np.float32)

        query_norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
        candidate_norms = np.linalg.norm(candidate_vectors, axis=1, keepdims=True)

        safe_query_norms = np.where(query_norms == 0, 1.0, query_norms)
        safe_candidate_norms = np.where(candidate_norms == 0, 1.0, candidate_norms)

        dot_product = query_vectors @ candidate_vectors.T
        normalized = dot_product / (safe_query_norms * safe_candidate_norms.T)

        return np.asarray(normalized, dtype=np.float32)

    def clear_model(self):
        self.embedding = None


embeddingmodelstate = EmbeddingModelState()