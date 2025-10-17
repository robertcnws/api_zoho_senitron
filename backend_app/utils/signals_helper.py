from django.core.cache import cache

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def cache_delete_keys(keys):
    for k in keys or []:
        cache.delete(k)

def cache_delete_patterns(patterns):
    if not patterns:
        return
    try:
        from django_redis import get_redis_connection
        con = get_redis_connection("default")
        for p in patterns:
            for key in con.scan_iter(p):
                con.delete(key)
    except Exception:
        pass


def channels_group_send(group, event):
    """Envía al channel layer si está disponible (dentro de on_commit)."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(group, event)
    except Exception:
        pass