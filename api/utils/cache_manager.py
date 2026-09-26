from cachetools import TTLCache
from functools import wraps
import hashlib
import json
from typing import Any, Callable

class CacheManager:
    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get_cache_key(self, *args, **kwargs) -> str:
        key_parts = []
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                key_parts.append(f"{key}={json.dumps(value, sort_keys=True)}")
            else:
                key_parts.append(f"{key}={str(value)}")
        combined = "|".join(key_parts)
        return hashlib.md5(combined.encode()).hexdigest()

    def cached(self, ttl: int = 300):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self.get_cache_key(func.__name__, *args, **kwargs)
                if cache_key in self.cache:
                    return self.cache[cache_key]
                result = func(*args, **kwargs)
                self.cache[cache_key] = result
                return result
            return wrapper
        return decorator
