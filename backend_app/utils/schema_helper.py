from datetime import date as date_cls, datetime, timedelta, timezone as dt_tz
from django.utils import timezone


def _parse_yyyy_mm_dd(s: str) -> "date_cls":
    return date_cls.fromisoformat(s)


def _day_bounds_aware(ymd: str):
    y, m, d = map(int, ymd.split('-'))
    start = datetime(y, m, d, 0, 0, 0, tzinfo=dt_tz.utc)         # 00:00Z
    end_excl = start + timedelta(days=1)                         # next day 00:00Z (exclusivo)
    return start, end_excl

def datetime_to_timezone(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dt_tz.utc)
    try:
        local_dt = dt.astimezone(timezone.get_default_timezone())
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return dt