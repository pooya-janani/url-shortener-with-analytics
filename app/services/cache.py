import redis
import os
from datetime import datetime
from app.repositories import short_link_repository

# Read from environment variables
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

DEFAULT_TTL = 120  # seconds

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

def get_original_url_from_cache(short_code: str, db, default_ttl: int = DEFAULT_TTL):
    """
    1. Try Redis cache
    2. If miss, query DB and populate Redis
    """
    # Step 1: check Redis
    original_url = r.get(short_code)
    if original_url:
        return original_url

    # Step 2: cache miss → query DB
    db_record = short_link_repository.get_short_link_by_code(db, short_code)
    if not db_record or not db_record.is_active:
        return None

    # Step 3: set TTL aligned with expiration
    ttl = default_ttl
    if db_record.expires_at:
        remaining = (db_record.expires_at - datetime.now(datetime.timezone.utc)).total_seconds()
        if remaining > 0:
            ttl = int(remaining)
        else:
            return None  # expired

    r.setex(short_code, ttl, db_record.original_url)
    return db_record.original_url


def refresh_hot_link(short_code: str, extra_ttl: int = 300):
    """
    If a link is accessed near expiration, extend its TTL
    """
    current_ttl = r.ttl(short_code)
    if current_ttl != -2 and current_ttl < 60:  # key exists and <1 min remaining
        r.expire(short_code, current_ttl + extra_ttl)