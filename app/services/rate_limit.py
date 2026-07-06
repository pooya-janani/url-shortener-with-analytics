import time
from fastapi import HTTPException, status
from app.services.cache import r

# Limits
UNAUTH_LIMIT = 100       # requests per minute
AUTH_LIMIT = 1000        # requests per minute
WINDOW = 60              # 1 minute window


def check_rate_limit(key: str, is_authenticated: bool):
    """
    Checks and increments the request count for a given key in Redis.
    Raises HTTP 429 if limit exceeded.
    """
    limit = AUTH_LIMIT if is_authenticated else UNAUTH_LIMIT
    redis_key = f"rate:{key}"

    # Increment request count atomically
    count = r.incr(redis_key)
    if count == 1:
        # first request, set expiration to WINDOW seconds
        r.expire(redis_key, WINDOW)

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({limit} requests per {WINDOW} seconds)"
        )