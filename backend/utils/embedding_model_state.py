from sentence_transformers import SentenceTransformer

class EmbeddingModelState:
    def __init__(self):
        self.embedding = None

    def load_embedding(self):
        self.embedding = SentenceTransformer("BAAI/bge-small-en-v1.5")

    def get_model(self):
        if self.embedding:
            return self.embedding
        else:
            return None

    def clear_model(self):
        self.embedding = None

embeddingmodelstate = EmbeddingModelState()