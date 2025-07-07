from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
import uvicorn
import os
import logging
from functools import lru_cache
import time
from collections import defaultdict
from rating_fetcher import RatingFetcher
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Security
security = HTTPBearer()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    logger.error("API_KEY environment variable is required")
    raise ValueError("API_KEY environment variable is required")

logger.info("Starting CPStats API...")

# Rate limiting
request_counts = defaultdict(list)
RATE_LIMIT = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))

# Rate limiting
request_counts = defaultdict(list)
RATE_LIMIT = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key for authentication"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


def rate_limit_check(client_ip: str):
    """Check if client has exceeded rate limit"""
    now = time.time()
    # Clean old requests
    request_counts[client_ip] = [req_time for req_time in request_counts[client_ip]
                                 if now - req_time < RATE_WINDOW]

    if len(request_counts[client_ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    request_counts[client_ip].append(now)


app = FastAPI(
    title="CPStats-API",
    description="REST API for fetching competitive programming ratings from multiple platforms",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG",
                                  "False").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("DEBUG",
                                    "False").lower() == "true" else None
)

# CORS middleware with strict origins for production
allowed_origins = []
origins_env = os.getenv("ALLOWED_ORIGINS", "")
if origins_env:
    allowed_origins = [origin.strip() for origin in origins_env.split(",")]
else:
    # Default to restrictive CORS in production
    allowed_origins = ["https://discord.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Cache for ratings (simple in-memory cache)


@lru_cache(maxsize=1000)
def cached_single_rating(platform: str, username: str, cache_key: int):
    """Cached version of single rating fetch"""
    return rating_fetcher.get_rating_by_platform(platform, username)


def get_cache_key():
    """Generate cache key based on current time (5 minute intervals)"""
    return int(time.time() // 300)  # 5 minutes


# Initialize rating fetcher
rating_fetcher = RatingFetcher()

# Pydantic models for request validation


class RatingRequest(BaseModel):
    platform: str
    username: str


class MultipleRatingRequest(BaseModel):
    requests: List[RatingRequest]


class SingleRatingRequest(BaseModel):
    platform: str
    username: str


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CPStats API",
        "version": "1.0.0",
        "status": "online",
        "supported_platforms": ["leetcode", "codeforces", "codechef"],
        "endpoints": {
            "single_rating": "/rating/{platform}/{username}",
            "multiple_ratings": "/ratings (POST)",
            "health": "/health",
            "platforms": "/platforms"
        },
        "rate_limit": f"{RATE_LIMIT} requests per {RATE_WINDOW//60} minutes"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with system information"""
    try:
        # Basic health check
        health_data = {
            "status": "healthy",
            "message": "API is running",
            "timestamp": int(time.time()),
            "version": "1.0.0"
        }

        # Add environment info (non-sensitive)
        health_data["environment"] = {
            "debug": os.getenv("DEBUG", "False").lower() == "true",
            "cache_enabled": os.getenv("ENABLE_CACHE", "True").lower() == "true",
            "rate_limit": f"{RATE_LIMIT} requests per {RATE_WINDOW//60} minutes"
        }

        return health_data
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/rating/{platform}/{username}")
async def get_single_rating(
    platform: str,
    username: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get rating for a single platform and username (Requires API key)

    - **platform**: Platform name (leetcode, codeforces, codechef)
    - **username**: Username on the platform
    """
    try:
        # Use cache if enabled
        if os.getenv("ENABLE_CACHE", "True").lower() == "true":
            cache_key = get_cache_key()
            result = cached_single_rating(platform, username, cache_key)
        else:
            result = rating_fetcher.get_rating_by_platform(platform, username)

        return result
    except Exception as e:
        logger.error(f"Error fetching single rating: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error")


@app.post("/ratings")
async def get_multiple_ratings(
    request: MultipleRatingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Get ratings for multiple platform/username pairs (Requires API key)

    Request body should contain a list of platform/username pairs with API key
    """
    try:
        if not request.requests:
            raise HTTPException(status_code=400, detail="No requests provided")

        if len(request.requests) > 20:  # Limit batch size
            raise HTTPException(
                status_code=400, detail="Maximum 20 requests per batch")

        # Convert Pydantic models to dicts
        requests_data = [req.dict() for req in request.requests]

        result = rating_fetcher.get_multiple_ratings(requests_data)
        return result
    except Exception as e:
        logger.error(f"Error fetching multiple ratings: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error")


@app.post("/rating")
async def get_single_rating_post(
    request: SingleRatingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Get rating for a single platform and username (POST method, Requires API key)
    """
    try:
        if os.getenv("ENABLE_CACHE", "True").lower() == "true":
            cache_key = get_cache_key()
            result = cached_single_rating(
                request.platform, request.username, cache_key)
        else:
            result = rating_fetcher.get_rating_by_platform(
                request.platform, request.username)

        return result
    except Exception as e:
        logger.error(f"Error fetching single rating (POST): {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error")


@app.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms"""
    return {
        "platforms": [
            {
                "name": "leetcode",
                "description": "LeetCode competitive programming platform",
                "rating_type": "Contest rating"
            },
            {
                "name": "codeforces",
                "description": "Codeforces competitive programming platform",
                "rating_type": "Contest rating"
            },
            {
                "name": "codechef",
                "description": "CodeChef competitive programming platform",
                "rating_type": "Contest rating"
            }
        ]
    }

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    # Use port 7860 for Hugging Face Spaces, 8000 as fallback
    port = int(os.getenv("PORT", os.getenv("API_PORT", "7860")))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    # For production/container environments, don't use reload
    if debug and os.getenv("CONTAINER_ENV") != "true":
        uvicorn.run("main:app", host=host, port=port, reload=True)
    else:
        uvicorn.run(app, host=host, port=port)
