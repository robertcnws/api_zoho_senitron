import time
from django.core.cache import cache
from datetime import datetime, timedelta, timezone as dtz

def token_bucket(name: str, rate: int = 60, per: int = 60) -> bool:
    now = int(time.time())
    window = now // per
    key = f"rl:{name}:{window}"
    val = cache.get(key)
    if val is None:
        cache.set(key, 1, timeout=per)
        return True
    if val >= rate:
        return False
    cache.incr(key)
    return True

def backoff(retries: int) -> int:
    return min(2 ** max(retries, 0), 60)

def allow_request(key="zoho", rps=2, window=1):
    bucket_key = f"rl:{key}:{int(time.time() // window)}"
    count = cache.incr(bucket_key) if cache.get(bucket_key) else (cache.set(bucket_key, 1, timeout=window) or 1)
    return count <= (rps * window)

def sleep_until_allowed(key="zoho", rps=2, window=1):
    while not allow_request(key, rps, window):
        time.sleep(0.05)
        
def _secs_to_midnight_utc():
    now = datetime.now(dtz.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())

def daily_quota_allow(key: str, limit: int) -> bool:
    k = f"quota:{key}:utcday"
    val = cache.get(k)
    if val is None:
        cache.add(k, 0, timeout=_secs_to_midnight_utc())
        val = 0
    return val < limit

def daily_quota_inc(key: str, n: int = 1):
    k = f"quota:{key}:utcday"
    ttl = _secs_to_midnight_utc()
    cache.add(k, 0, timeout=ttl)
    cache.incr(k, n)
