from datetime import datetime, timedelta
import json

# Phase 1: in-memory
_cache: dict[str, tuple[dict, datetime]] = {}

async def get_cached(key: str) -> dict | None:
    """Return cached value if exists and not expired. None otherwise."""
    if key in _cache:
        val, expiry = _cache[key]
        if datetime.now() < expiry:
            return val
        else:
            del _cache[key]
    return None

async def set_cached(key: str, value: dict, ttl_seconds: int = 3600) -> None:
    """Store value with expiry timestamp."""
    expiry = datetime.now() + timedelta(seconds=ttl_seconds)
    _cache[key] = (value, expiry)

async def invalidate(key: str) -> None:
    """Remove a specific cache entry."""
    if key in _cache:
        del _cache[key]
