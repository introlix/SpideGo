from sentence_transformers import SentenceTransformer

class EmbeddingModelState:
    def __init__(self):
        self.embedding = None

    def load_embedding(self):
        self.embedding = SentenceTransformer("all-MiniLM-L6-v2")

    def get_model(self):
        if self.embedding:
            return self.embedding
        else:
            return None

    def clear_model(self):
        self.embedding = None

embeddingmodelstate = EmbeddingModelState()