import json
from django_redis import get_redis_connection

def get_or_set_cache(key, callback, timeout=300):
    
    redis_conn = get_redis_connection("default")

    cached_value = redis_conn.get(key)
    if cached_value:
        return json.loads(cached_value)

    # Compute fresh value
    value = callback()

    # Save to Redis
    redis_conn.set(key, json.dumps(value), ex=timeout)
    return value

class MyRedis:
    def __init__(self):
        self.redis_conn = get_redis_connection("default")
        
    def get(self, key):
        cached_value = self.redis_conn.get(key)
        if cached_value:
            return json.loads(cached_value)
        
    
    def set(self, key, value, timeout=300):
        self.redis_conn.set(key, json.dumps(value), ex=timeout)
        return value
    
    def incr(self, key, amount=1):
        self.redis_conn.incr(key, amount)
    
    def decr(self, key, amount):
        self.redis_conn.decr(key, amount)
        
    
myredis = MyRedis()

        
