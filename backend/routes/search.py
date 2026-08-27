from fastapi import APIRouter, HTTPException, status
from backend.search import search as search_fn

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
async def search(query: str, tab: str):
    try:
        res = await search_fn(query, tab)
        
        if not res or "results" not in res:
            return {"results": []}

        results = []
        for r in res["results"]:
            results.append({
                "title": r.get("title"),
                "content": r.get("content"),
                "url": r.get("url"),
                "engine": r.get("engine"),
                "thumbnail_src": r.get("thumbnail_src"),
                "thumbnail": r.get("thumbnail"),
                "img_src": r.get("img_src"),
                "publishedDate": r.get("publishedDate")
            })
            
        return {"results": results}

    except Exception as e:
        error_msg = str(e)

        if "ValidationException" in error_msg or "Invalid value" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed search preferences detected"
            )

        if "CaptchaException" in error_msg or "CAPTCHA" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Upstream search engines are temporarily rate-limiting requests (CAPTCHA triggered)."
            )

        if "Timeout" in error_msg or "ConnectTimeout" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The search engines took too long to respond. Please try again."
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected search error occurred: {error_msg}"
        )
