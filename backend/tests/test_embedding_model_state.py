from backend.utils.embedding_model_state import EmbeddingModelState


def test_load_embedding_uses_fastembed(monkeypatch):
    created = {}

    class FakeTextEmbedding:
        def __init__(self, model_name):
            created["model_name"] = model_name

    monkeypatch.setattr(
        "backend.utils.embedding_model_state.TextEmbedding",
        FakeTextEmbedding,
    )

    state = EmbeddingModelState()
    state.load_embedding()

    assert isinstance(state.embedding, FakeTextEmbedding)
    assert created["model_name"] == "BAAI/bge-small-en-v1.5"
