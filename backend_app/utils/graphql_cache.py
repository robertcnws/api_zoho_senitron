# utils/graphql_cache.py
from django.core.cache import cache

def get_or_build_list(cache_key: str, builder, ttl: int = 120):
    data = cache.get(cache_key)
    if data is not None:
        return data
    data = builder()
    cache.set(cache_key, data, ttl)
    return data
