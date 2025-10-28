import json
import requests
import os
import re
import time
from django.db import transaction
from django.db.utils import OperationalError
from datetime import datetime as dt
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import HTTPError, Timeout, ConnectionError

# =========================================================
#                     HTTP / AUTH HELPERS
# =========================================================

def config_headers():
    headers = {}
    api_token = os.getenv("API_AUTH_TOKEN", "0b7ad1e0-776e-4267-a509-55d8d3d2c19c")
    headers["Authorization"] = f"Token {api_token}"  # o "Bearer ..."
    headers["Content-Type"] = "application/json"
    return headers

def _session_with_retry():
    s = requests.Session()
    r = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        backoff_factor=0.5,
    )
    a = HTTPAdapter(max_retries=r)
    s.mount("https://", a)
    s.mount("http://", a)
    return s

def api_get(session, url, params=None, timeout=20):
    resp = session.get(url, headers=config_headers(), params=params or {}, timeout=timeout)
    resp.raise_for_status()
    return resp

def api_post_json(session, url, payload: dict, timeout=40):
    resp = session.post(url, headers=config_headers(), data=json.dumps(payload), timeout=timeout)
    resp.raise_for_status()
    return resp

# =========================================================
#                           UTILS
# =========================================================

def _retryable(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        status = getattr(getattr(exc, "response", None), "status_code", None)
        return status == 429 or (status is not None and 500 <= status < 600)
    return isinstance(exc, (Timeout, ConnectionError))

# --- Normalización de timestamps ISO sin zona (preservando valor completo) --

_ISO_NO_TZ_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$')

def _ensure_iso_with_tz(s: str):
    """
    Si es ISO con 'T' pero SIN 'Z' ni offset, devuelve con '+00:00'.
    Si trae 'Z', lo convertimos a '+00:00' para uniformidad.
    No recorta nada, solo asegura zona.
    """
    if not isinstance(s, str):
        return s
    t = s.strip()
    if 'T' not in t:
        return t
    if t.endswith('Z'):
        return t[:-1] + '+00:00'
    tail = t[-6:]
    if ('+' in tail or '-' in tail) and ':' in tail:
        return t  # ya tiene offset tipo +05:30 o -04:00
    if _ISO_NO_TZ_RE.match(t):
        return t + '+00:00'
    if '+' not in t and '-' not in t[-6:] and not t.endswith('+00:00'):
        return t + '+00:00'
    return t

def _sanitize_datetime_strings_inplace(d: dict):
    """
    Normaliza en sitio todas las claves cuyo valor parezca ISO con 'T' sin zona horaria.
    (No recorta valores; solo agrega zona si falta.)
    """
    if not isinstance(d, dict):
        return d
    for k, v in list(d.items()):
        if isinstance(v, str) and 'T' in v:
            d[k] = _ensure_iso_with_tz(v)
    return d
# ---------------------------------------------------------------------------

def _iso_to_aware(v: str | None):
    """
    Parse tolerante: asume UTC si no hay zona (mediante _ensure_iso_with_tz).
    No altera el valor de entrada salvo agregar zona si falta.
    """
    if not v:
        return None
    try:
        return dt.fromisoformat(_ensure_iso_with_tz(v))
    except Exception:
        return None

def _ensure_date_str(date_str: str | None) -> str | None:
    """
    Garantiza formato YYYY-MM-DD para parámetros de filtro (start_date/end_date).
    NO se usa para campos de datos; solo para query params a la API.
    """
    if not date_str:
        return None
    try:
        return dt.fromisoformat(date_str[:10]).strftime("%Y-%m-%d")
    except Exception:
        if len(date_str) >= 10 and date_str[4] == "-" and date_str[7] == "-":
            return date_str[:10]
        raise ValueError(f"Fecha inválida, espera YYYY-MM-DD: {date_str}")

def run_with_deadlock_retry(fn, max_retries=5):
    tries = 0
    while True:
        tries += 1
        try:
            with transaction.atomic():
                return fn()
        except OperationalError as e:
            if "40P01" in str(e) and tries < max_retries:
                time.sleep(min(0.1 * (2 ** (tries - 1)), 2.0))
                continue
            raise

def upsert_on_conflict(Model, objs, unique_fields, update_fields, batch_size=100, max_retries=5):
    if not objs:
        return 0
    def _do():
        Model.objects.bulk_create(
            objs,
            batch_size=batch_size,
            ignore_conflicts=False,
            update_conflicts=True,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )
        return len(objs)
    return run_with_deadlock_retry(_do, max_retries=max_retries)


def _pick_ts(obj, fields=("last_modified_time", "created_time")):
    for f in fields:
        v = getattr(obj, f, None)
        if v:
            return v
    return None

def dedupe_model_instances(logger, instances, key_attr: str, newer_wins=True, ts_fields=("last_modified_time", "created_time")):
    """
    Deduplica una lista de modelos por `key_attr` (p.ej. 'shipment_id'/'package_id').
    Si `newer_wins` es True, conserva la instancia con timestamp más reciente.
    """
    if not instances:
        return instances
    by_key = {}
    dup_count = 0
    for obj in instances:
        key = getattr(obj, key_attr, None)
        if not key:
            continue
        if key not in by_key:
            by_key[key] = obj
        else:
            dup_count += 1
            if newer_wins:
                cur = by_key[key]
                t_cur = _pick_ts(cur, ts_fields)
                t_new = _pick_ts(obj, ts_fields)
                # si no hay ts, deja la existente; si hay ambos, gana la más reciente
                if t_new and (not t_cur or (t_new > t_cur)):
                    by_key[key] = obj
            # si newer_wins=False, se queda la primera
    if dup_count:
        logger.warning(f"[UPSERT] Deduplicated {dup_count} duplicate '{key_attr}' values in batch ({len(instances)} -> {len(by_key)})")
    return list(by_key.values())