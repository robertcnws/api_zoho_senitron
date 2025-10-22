from django.core.cache import cache
from django.utils import timezone
from datetime import datetime
import random, time

def get_cursor(name: str):
    ts = cache.get(f"cursor:{name}")
    if not ts:
        return None
    try:
        # ISO 8601 -> datetime
        dt = datetime.fromisoformat(ts)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except Exception:
        return None

def set_cursor(name: str, dt):
    if not dt:
        return
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    cache.set(f"cursor:{name}", dt.isoformat(), timeout=None)
    

def _run_lock(name: str, ttl=300):
    key = f"lock:{name}"
    if not cache.add(key, "1", timeout=ttl):
        return None
    return key

def _release_lock(key):
    if key:
        cache.delete(key)
        
def _jitter_sleep(max_seconds: float):
    time.sleep(random.uniform(0, max_seconds))
