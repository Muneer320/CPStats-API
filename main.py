"""HTTP interface for the historical CPStats ratings service."""

from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import os
import secrets
import time

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from rating_fetcher import PLATFORMS, RatingFetcher

load_dotenv()
API_KEY = os.getenv("API_KEY", "")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "900"))
if min(RATE_LIMIT, RATE_WINDOW, CACHE_TTL) < 1:
    raise ValueError("Rate and cache settings must be positive")

app = FastAPI(title="CPStats API", version="1.1.0",
              description="Best-effort public ratings lookup for a historical Discord project")
origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "").split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
security = HTTPBearer(auto_error=False)
fetcher = RatingFetcher()
rate_counts = defaultdict(deque)
rate_lock = Lock()
cache = {}
cache_lock = Lock()


class RatingRequest(BaseModel):
    platform: str = Field(min_length=1, max_length=32)
    username: str = Field(min_length=1, max_length=64)


class MultipleRatingRequest(BaseModel):
    requests: list[RatingRequest] = Field(min_length=1, max_length=20)


def authenticated(request: Request, credentials: HTTPAuthorizationCredentials | None = Security(security)):
    if not API_KEY:
        raise HTTPException(503, "API key is not configured")
    if credentials is None or not secrets.compare_digest(credentials.credentials, API_KEY):
        raise HTTPException(401, "Invalid API key")
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with rate_lock:
        timestamps = rate_counts[ip]
        while timestamps and now - timestamps[0] >= RATE_WINDOW:
            timestamps.popleft()
        if len(timestamps) >= RATE_LIMIT:
            raise HTTPException(429, "Rate limit exceeded")
        timestamps.append(now)


def lookup(platform: str, username: str):
    platform, username = platform.lower().strip(), username.strip()
    if platform not in PLATFORMS:
        raise HTTPException(400, "Unsupported platform")
    if not username or len(username) > 64:
        raise HTTPException(400, "Invalid username")
    key = (platform, username)
    now = time.monotonic()
    with cache_lock:
        cached = cache.get(key)
        if cached and cached[0] > now and os.getenv("ENABLE_CACHE", "true").lower() == "true":
            return cached[1]
    result = fetcher.get_rating_by_platform(platform, username)
    status = result.get("status")
    if status == "user_not_found":
        raise HTTPException(404, "User not found")
    if status != "success":
        raise HTTPException(502, "Platform lookup failed")
    if os.getenv("ENABLE_CACHE", "true").lower() == "true":
        with cache_lock:
            cache[key] = (now + CACHE_TTL, result)
            if len(cache) > 1000:
                for stale in list(cache)[:100]:
                    cache.pop(stale, None)
    return result


@app.get("/")
def root():
    return {"service": "CPStats API", "version": "1.1.0", "platforms": PLATFORMS,
            "status": "historical project", "health": "/health"}


@app.get("/health")
def health():
    if not API_KEY:
        raise HTTPException(503, "API key is not configured")
    return {"status": "healthy", "version": "1.1.0"}


@app.get("/platforms")
def platforms():
    return {"platforms": list(PLATFORMS)}


@app.get("/rating/{platform}/{username}", dependencies=[Depends(authenticated)])
def single_get(platform: str, username: str):
    return lookup(platform, username)


@app.post("/rating", dependencies=[Depends(authenticated)])
def single_post(request: RatingRequest):
    return lookup(request.platform, request.username)


@app.post("/ratings", dependencies=[Depends(authenticated)])
def batch(request: MultipleRatingRequest):
    # Blocking requests run in a worker pool; each item has its own error status.
    items = [item.model_dump() for item in request.requests]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda item: fetcher.get_rating_by_platform(**item), items))
    return {"results": results, "total_requests": len(results),
            "successful_requests": sum(item.get("status") == "success" for item in results)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("PORT", "7860")))
