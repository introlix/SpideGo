from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.suggestions import router as search_suggestions

app = FastAPI(title="SpideGo", openapi_prefix="/api/v1")

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