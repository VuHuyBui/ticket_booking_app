import redis
import logging
from django.conf import settings
import hashlib

r = redis.Redis(
    host="127.0.0.1",
    port=6379,
    decode_responses=True,
    socket_timeout=5,     # avoid hanging
    socket_connect_timeout=5
)

logger = logging.getLogger(__name__)

def make_cache_key(prefix: str, identifier: str) -> str:
    """
    Generate a safe cache key, e.g. "response:somehash"
    """
    return f"{prefix}:{hashlib.md5(identifier.encode()).hexdigest()}"

def get_key(key, value=None):
    try:
        if not r.exists(key) and value is not None:
            r.setnx(key, value)
        return r.get(key)
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error while getting key {key}: {e}")
        return None   # or some default fallback


def set_key(key, value):
    try:
        r.set(key, value)
        return True
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error while setting key {key}: {e}")
        return False
