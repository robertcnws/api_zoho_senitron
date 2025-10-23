from django.conf import settings
from django.db import transaction
from django.utils import timezone
from dateutil.parser import parse
from django.db.models import Q
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4

from .models import (
    SenitronItem,
    SenitronItemAsset,
    TimelineItem,
    SenitronStatus,
    SenitronItemAssetLogs,
)
from api_zoho.models import ZohoInventoryItem, JobsUpdatingTimes
from .manage_instances import (
    create_inventory_item_instance,
    create_inventory_item_asset_instance,
    create_inventory_item_asset_logs_instance,
)
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests
import logging

logger = logging.getLogger(__name__)

MAX_WORKERS = 10
BATCH_SIZE = 500
REQUEST_TIMEOUT = 10


def _create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504], allowed_methods=["GET", "POST"])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def sync_senitron_inventory_items(item_number=None):
    params = {"api_key": settings.API_KEY_SENITRON, "per_page": 1000, "page": 1}
    if item_number:
        params["item_number"] = item_number

    url = settings.API_SENITRON_QUANTITIES_URL
    session = _create_session()

    items_to_get = []
    resp = session.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    items_to_get.extend(data.get("items", []))
    total_pages = data.get("total_pages", 1)

    current_page = 1
    while current_page < total_pages:
        current_page += 1
        params["page"] = current_page
        r = session.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        items_to_get.extend(data.get("items", []))

    item_ids = [it["item_number"] for it in items_to_get]
    existing_items = SenitronItem.objects.filter(item_number__in=item_ids)
    existing_ids = set(existing_items.values_list("item_number", flat=True))

    new_items = []
    to_update = []

    for raw in items_to_get:
        obj = create_inventory_item_instance(logger, raw)
        zoho_item = ZohoInventoryItem.objects.filter(item_id=obj.item_number).first()
        sku_info = f"SKU: {zoho_item.sku}, " if zoho_item and zoho_item.sku else ""
        if obj.item_number in existing_ids:
            prev = existing_items.get(item_number=obj.item_number)
            to_update.append(obj)
            if int(prev.qty) != int(obj.qty):
                TimelineItem.objects.create(
                    item_number=obj.item_number,
                    previous_quantity=prev.qty,
                    date_previous_quantity=datetime.now(),
                    actual_quantity=obj.qty,
                    date_actual_quantity=datetime.now(),
                    zoho_item=zoho_item if zoho_item else None,
                    senitron_item=prev,
                    text=f"Senitron Item ({sku_info}ID: {obj.item_number}) quantity changed from {prev.qty} to {obj.qty}",
                )
        else:
            new_items.append(obj)
            TimelineItem.objects.create(
                item_number=obj.item_number,
                actual_quantity=obj.qty,
                date_actual_quantity=datetime.now(),
                zoho_item=zoho_item if zoho_item else None,
                senitron_item=None,
                text=f"Senitron Item ({sku_info}ID: {obj.item_number}, Qty: {obj.qty}) created",
            )

    with transaction.atomic():
        if new_items:
            SenitronItem.objects.bulk_create(new_items, batch_size=200, ignore_conflicts=True)
        if to_update:
            SenitronItem.objects.bulk_update(to_update, fields=["tags_count", "qty"], batch_size=1000)

    JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
    JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    return {"created": len(new_items), "updated": len(to_update)}


def sync_senitron_inventory_item_assets(item_number=None, assets_hint=None):
    data_assets_hint = assets_hint or []
    params = {"api_key": settings.API_KEY_SENITRON, "per_page": 250}
    if item_number:
        params["item_number"] = item_number

    # caches base
    existing_statuses = SenitronStatus.objects.all()
    status_cache = {(s.name, s.senitron_id): s for s in existing_statuses}

    item_numbers = {it["item_number"] for it in data_assets_hint if "item_number" in it}
    existing_items = SenitronItem.objects.filter(item_number__in=item_numbers)
    item_cache = {it.item_number: it for it in existing_items}

    url = settings.API_SENITRON_ASSETS_URL
    session = _create_session()

    def fetch_page(page):
        page_params = dict(params)
        page_params["page"] = page
        r = session.get(url, params=page_params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        items = r.json().get("assets", [])
        if "item_number" in page_params and item_numbers:
            items = [it for it in items if it.get("item_number") in item_numbers]
        return items, len(items) > 0
    
    page = 1
    has_more = True
    raw_assets = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        while has_more:
            futures = {ex.submit(fetch_page, p): p for p in range(page, page + MAX_WORKERS)}
            has_more = False
            for f in as_completed(futures):
                items, ok = f.result()
                if items:
                    raw_assets.extend(items)
                if ok:
                    has_more = True
            page += MAX_WORKERS
    
    key_list = []
    assets_to_insert = []
    for raw in raw_assets:
        obj = create_inventory_item_asset_instance(logger, raw, status_cache, item_cache)
        if not obj:
            continue
        
        if getattr(obj, "location", None) and not getattr(obj, "last_zone", None):
            obj.last_zone = getattr(obj, "location")
        
        if getattr(obj, "updated_time", None) and not getattr(obj, "updated_at", None):
            obj.updated_at = getattr(obj, "updated_time")
        
        if getattr(obj, "read", None) is None:
            obj.read = False

        key = (obj.serial_number, obj.item_number)
        key_list.append(key)
        assets_to_insert.append(obj)
    
    existing_map = {}
    
    if key_list:
        for i in range(0, len(key_list), BATCH_SIZE):
            chunk = key_list[i:i + BATCH_SIZE]
            cond = Q()
            for sn, inum in chunk:
                cond |= Q(serial_number=sn, item_number=inum)
            for a in SenitronItemAsset.objects.filter(cond):
                existing_map[(a.serial_number, a.item_number)] = a

    to_create, to_update = [], []
    
    scope_item_numbers = {inum for _, inum in key_list if inum}

    for obj in assets_to_insert:
        k = (obj.serial_number, obj.item_number)
        prev = existing_map.get(k)
        if prev:
            if getattr(obj, "status", None) is not None:
                prev.status = obj.status
            elif getattr(obj, "status_id", None) is not None:
                prev.status_id = obj.status_id
            
            if getattr(obj, "last_zone", None) is not None:
                prev.last_zone = obj.last_zone

            if getattr(obj, "read", None) is not None:
                prev.read = bool(obj.read)

            if getattr(obj, "updated_at", None) is not None:
                prev.updated_at = obj.updated_at

            if getattr(obj, "date_read", None) is not None:
                prev.date_read = obj.date_read
                
            for attr in ("first_seen", "last_seen", "last_seen_antenna", "epc", "alt_serial"):
                if getattr(obj, attr, None) is not None:
                    setattr(prev, attr, getattr(obj, attr))

            to_update.append(prev)
        else:
            to_create.append(obj)

    with transaction.atomic():
        if to_create:
            SenitronItemAsset.objects.bulk_create(
                to_create, batch_size=BATCH_SIZE, ignore_conflicts=True
            )

        if to_update:
            SenitronItemAsset.objects.bulk_update(
                to_update,
                fields=[
                    "status",          
                    "last_zone",       
                    "read",
                    "updated_at",      
                    "date_read",
                    "first_seen",
                    "last_seen",
                    "last_seen_antenna",
                    "epc",
                    "alt_serial",
                ],
                batch_size=BATCH_SIZE,
            )
        
        if key_list and scope_item_numbers:
            keep_pairs = set(key_list)
            
            ids_to_delete = []
            for inum in scope_item_numbers:
                qs = SenitronItemAsset.objects.filter(item_number=inum).only("id", "serial_number", "item_number")
                for a in qs:
                    if (a.serial_number, a.item_number) not in keep_pairs:
                        ids_to_delete.append(a.id)
            
            for i in range(0, len(ids_to_delete), BATCH_SIZE):
                chunk = ids_to_delete[i:i + BATCH_SIZE]
                SenitronItemAsset.objects.filter(id__in=chunk).delete()

        # housekeeping
        JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
        JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    return {"created": len(to_create), "updated": len(to_update), "total": len(key_list)}


def sync_senitron_inventory_item_assets_logs(item_number=None):
    now = timezone.now()
    last = SenitronItemAssetLogs.objects.order_by("-created_time").first()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    diff = now - last.created_time if last else now - start_of_day
    diff_hours = int(max(diff.total_seconds() // 3600, 1))

    params = {"api_key": settings.API_KEY_SENITRON, "per_page": 250, "filter_hours": diff_hours}
    if item_number:
        params["item_number"] = item_number

    url = settings.API_SENITRON_ASSETS_LOGS_URL
    session = _create_session()

    def fetch_page(page):
        page_params = dict(params)
        page_params["page"] = page
        r = session.get(url, params=page_params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json().get("assets", []), True if r.json().get("assets", []) else False

    page = 1
    has_more = True
    raw_logs = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        while has_more:
            futures = {ex.submit(fetch_page, p): p for p in range(page, page + MAX_WORKERS)}
            has_more = False
            for f in as_completed(futures):
                items, ok = f.result()
                if items:
                    raw_logs.extend(items)
                if ok:
                    has_more = True
            page += MAX_WORKERS

    dedup = {}
    for it in raw_logs:
        sn = it.get("serial_number")
        cur = (it.get("current_status") or {}).get("id")
        last_s = (it.get("last_status") or {}).get("id")
        ls = it.get("last_seen")
        if not sn or not cur or not last_s or not ls:
            continue
        ts = parse(ls)
        key = (sn, last_s, cur)
        if key not in dedup or ts > dedup[key]["ts"]:
            dedup[key] = {"data": it, "ts": ts}

    objs = []
    for v in dedup.values():
        obj = create_inventory_item_asset_logs_instance(logger, v["data"])
        if obj:
            objs.append(obj)

    with transaction.atomic():
        if objs:
            SenitronItemAssetLogs.objects.bulk_create(objs, batch_size=BATCH_SIZE, ignore_conflicts=True)
        cutoff = now - timezone.timedelta(days=30)
        SenitronItemAssetLogs.objects.filter(created_time__lt=cutoff).delete()
        JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
        JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    return {"inserted": len(objs)}