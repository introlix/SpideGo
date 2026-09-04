from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.suggestions import router as search_suggestions
from backend.routes.search import router as search_router
from backend.routes.featured_snippets import router as featured_snippets_router
from backend.utils.embedding_model_state import embeddingmodelstate

@asynccontextmanager
async def lifespan(app: FastAPI):
    # adding embedding model to app state
    embeddingmodelstate.load_embedding()

    try:
        yield
    finally:
        embeddingmodelstate.clear_model()

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