from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.suggestions import router as search_suggestions
from backend.routes.search import router as search_router
from backend.routes.featured_snippets import router as featured_snippets_router
from backend.utils.embedding_model_state import embeddingmodelstate
from sentence_transformers import SentenceTransformer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # adding embedding model and pinecone client to app state
    embeddingmodelstate.embedding = SentenceTransformer("all-MiniLM-L6-v2")

    try:
        yield
    finally:
        # optional cleanup
        if hasattr(embeddingmodelstate, "embedding"):
            del embeddingmodelstate.embedding

app = FastAPI(title="SpideGo", openapi_prefix="/api/v1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "Content-Type",
        "X-API-Key",
        "Authorization",
    ],
)


app.include_router(search_suggestions)
app.include_router(search_router)
app.include_router(featured_snippets_router)