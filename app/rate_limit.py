"""
Rate limiting — protects Amazon SP-API-calling endpoints from abuse.

Uses slowapi (built on top of `limits`) to enforce per-client rate limits.
The rate key is derived from the X-API-Key header so each client gets its own
independent quota, preventing one client from exhausting limits for others.

Two tiers are exposed:
  - `rate_limit_amazon`  — strict (e.g. 3/minute) for endpoints that call Amazon
  - `rate_limit_standard` — looser (e.g. 10/minute) for read-heavy DB endpoints
"""

import logging

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Key function — identify clients by API key, fall back to IP
# ---------------------------------------------------------------------------

def _get_rate_limit_key(request: Request) -> str:
    """
    Extract the client identifier for rate-limiting.
    Prefers the X-API-Key header (each client gets its own bucket).
    Falls back to remote IP if no key is present.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use last 8 chars to avoid logging full keys
        return f"apikey:{api_key[-8:]}"
    return get_remote_address(request)


# ---------------------------------------------------------------------------
# Limiter instance
# ---------------------------------------------------------------------------

limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=[],                    # No blanket default — opt-in only
    storage_uri="memory://",              # In-process store; swap to Redis for multi-worker
    strategy="fixed-window",
)


# ---------------------------------------------------------------------------
# Custom 429 handler
# ---------------------------------------------------------------------------

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Return a clean JSON 429 response with Retry-After header.
    """
    retry_after = exc.detail.split("per")[-1].strip() if exc.detail else "a moment"

    logger.warning(
        "Rate limit exceeded for %s on %s %s",
        _get_rate_limit_key(request),
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Too many requests. Limit: {exc.detail}.",
            "message": (
                "This endpoint calls Amazon SP-API internally. "
                "Please wait before retrying to protect shared credentials."
            ),
        },
        headers={"Retry-After": retry_after},
    )
