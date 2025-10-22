import os, json, time, requests
from datetime import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from django.core.cache import cache

from .models import (
    AppConfig, ZohoInventoryItem, ZohoInventoryShipmentSalesOrder,
    ZohoShipmentOrder, ZohoPackage, ZohoItemAssetsTrack, JobsUpdatingTimes
)
from api_senitron.models import SenitronItem, TimelineItem
from .manage_instances import (
    create_inventory_item_instance, create_inventory_sales_order_instance,
    create_inventory_shipment_instance, create_inventory_package_instance,
    create_zoho_item_assets_track_instance
)
from common.rate_limit import (
    sleep_until_allowed, 
    daily_quota_allow, 
    daily_quota_inc
)
from api_senitron.views import create_notification

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ZOHO_TOKEN_KEY = "zoho:access_token"
ZOHO_TOKEN_LOCK = "zoho:access_token:lock"
ZOHO_RPS = int(os.getenv("ZOHO_RPS", "2"))
ZOHO_DAILY_SOFT_CAP = int(os.getenv("ZOHO_DAILY_SOFT_CAP", "11000"))
ZOHO_MAX_PAGES_PER_RUN = int(os.getenv("ZOHO_MAX_PAGES_PER_RUN", "4"))

class ZohoRateLimited(Exception):
    def __init__(self, retry_after=60, message="rate limited"):
        self.retry_after = retry_after
        super().__init__(message)

def _parse_last_modified(obj, fld="last_modified_time", fallback="created_time"):
    v = getattr(obj, fld, None)
    return v if v else getattr(obj, fallback, None)

def _iso_to_aware(ts):
    if not ts:
        return None
    try:
        return dt.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
    except Exception:
        return None

def _raise_if_rate_limited(resp):
    try:
        j = resp.json()
    except Exception:
        j = {}
    if resp.status_code == 429 or j.get("code") == 44:
        ra_hdr = resp.headers.get("Retry-After")
        ra = int(ra_hdr) if ra_hdr and ra_hdr.isdigit() else 60
        raise ZohoRateLimited(retry_after=max(ra, 60))

def _session_with_retry():
    s = requests.Session()
    r = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "POST"], backoff_factor=0.5)
    a = HTTPAdapter(max_retries=r)
    s.mount("https://", a)
    s.mount("http://", a)
    return s

def zoho_get(session, url, headers, params=None, timeout=15):
    if not daily_quota_allow("zoho", ZOHO_DAILY_SOFT_CAP):
        raise requests.RequestException("Daily soft cap reached")
    sleep_until_allowed(key="zoho", rps=ZOHO_RPS)
    resp = session.get(url, headers=headers, params=params or {}, timeout=timeout)
    if resp.status_code == 401:
        new_token = refresh_zoho_access_token()
        headers["Authorization"] = f"Zoho-oauthtoken {new_token}"
        sleep_until_allowed(key="zoho", rps=ZOHO_RPS)
        resp = session.get(url, headers=headers, params=params or {}, timeout=timeout)
    _raise_if_rate_limited(resp)
    daily_quota_inc("zoho", 1)
    return resp

def sync_inventory_items(*, item_number=None, username=None, updated_since=None):
    app_config = AppConfig.objects.first()
    headers = config_headers()
    if item_number:
        params = {"organization_id": app_config.zoho_org_id}
        url = f"{settings.ZOHO_INVENTORY_ITEMS_URL}/{item_number}"
    else:
        params = {"organization_id": app_config.zoho_org_id, "per_page": 200, "page": 1}
        url = settings.ZOHO_INVENTORY_ITEMS_URL

    items_to_get = []
    session = _session_with_retry()

    def fetch_page(p):
        cur = dict(params, page=p)
        resp = zoho_get(session, url, headers, cur)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", []), data.get("page_context", {}).get("has_more_page", False)

    def fetch_single():
        resp = zoho_get(session, url, headers, params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("item", {})

    if not item_number:
        page = 1
        has_more = True
        pages_fetched = 0 
        while has_more:
            if pages_fetched >= ZOHO_MAX_PAGES_PER_RUN:
                break
            page_items, has_more = fetch_page(page)
            if updated_since:
                trimmed, stop = [], False
                for it in page_items:
                    ts = _iso_to_aware(it.get("last_modified_time") or it.get("created_time"))
                    if ts and ts <= updated_since:
                        stop = True
                        break
                    trimmed.append(it)
                items_to_get.extend(trimmed)
                if stop:
                    break
            else:
                items_to_get.extend(page_items)
            page += 1
            pages_fetched += 1
            time.sleep(float(os.getenv("ZOHO_PAGE_SLEEP", "0.25")))
    else:
        single = fetch_single()
        if single:
            items_to_get.append(single)

    item_ids = [it["item_id"] for it in items_to_get]
    existing = ZohoInventoryItem.objects.filter(item_id__in=item_ids)
    existing_map = {it.item_id: it for it in existing}

    new_items, to_update, timelines = [], [], []
    max_ts, changed = None, False

    for data_item in items_to_get:
        new_obj = create_inventory_item_instance(None, data_item)
        prev = existing_map.get(new_obj.item_id)
        senitron_item = SenitronItem.objects.filter(item_number=new_obj.item_id).first()
        lm = _parse_last_modified(new_obj)
        if lm and (max_ts is None or lm > max_ts):
            max_ts = lm
        if prev:
            to_update.append(new_obj)
            if prev.status != new_obj.status:
                timelines.append(TimelineItem(
                    item_number=new_obj.item_id,
                    previous_status_zoho=prev.status,
                    date_previous_status_zoho=prev.last_modified_time or prev.created_time,
                    actual_status_zoho=new_obj.status,
                    date_actual_status_zoho=new_obj.last_modified_time or new_obj.created_time,
                    zoho_item=new_obj,
                    senitron_item=senitron_item,
                    text=f"{new_obj.sku or '-'} status changed -> From {prev.status} to {new_obj.status}"
                ))
            if int(prev.stock_on_hand) != int(new_obj.stock_on_hand):
                ch = "added" if new_obj.stock_on_hand > prev.stock_on_hand else "removed"
                absv = abs(new_obj.stock_on_hand - prev.stock_on_hand)
                timelines.append(TimelineItem(
                    item_number=new_obj.item_id,
                    previous_stock_on_hand=prev.stock_on_hand,
                    date_previous_stock_on_hand=prev.last_modified_time or prev.created_time,
                    actual_stock_on_hand=new_obj.stock_on_hand,
                    date_actual_stock_on_hand=new_obj.last_modified_time or new_obj.created_time,
                    zoho_item=new_obj,
                    senitron_item=senitron_item,
                    text=f"{new_obj.sku or '-'} : {int(absv)} unit(s) {ch} -> New stock on hand: {int(new_obj.stock_on_hand)}"
                ))
        else:
            new_items.append(new_obj)
            timelines.append(TimelineItem(
                item_number=new_obj.item_id,
                actual_stock_on_hand=new_obj.stock_on_hand,
                date_actual_stock_on_hand=new_obj.last_modified_time or new_obj.created_time,
                actual_status_zoho=new_obj.status,
                date_actual_status_zoho=new_obj.last_modified_time or new_obj.created_time,
                zoho_item=new_obj,
                senitron_item=senitron_item,
                text=f"{new_obj.sku or '-'} created -> On hand: {int(new_obj.stock_on_hand)}, Status: {new_obj.status}"
            ))

    with transaction.atomic():
        if new_items:
            ZohoInventoryItem.objects.bulk_create(new_items, batch_size=200, ignore_conflicts=True)
            changed = True
        if to_update:
            ZohoInventoryItem.objects.bulk_update(to_update, fields=["status", "stock_on_hand", "last_modified_time"], batch_size=200)
            changed = True
        if timelines:
            TimelineItem.objects.bulk_create(timelines, batch_size=200, ignore_conflicts=True)
        JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
        JobsUpdatingTimes.objects.create(last_updated=timezone.now())
    
    if username and changed:
        create_notification('zoho_item', 'has loaded new info from Zoho Items', 'load', username)
        create_notification('system_timeline', 'has added new info about timelines in Zoho Items', 'create_timeline', username)

    return {"changed": changed, "max_ts": max_ts}

def sync_inventory_sales_orders(*, start_date: str, end_date: str | None, username=None):
    app_config = AppConfig.objects.first()
    headers = config_headers()
    params = {"organization_id": app_config.zoho_org_id, "per_page": 200, "page": 1}
    if end_date:
        params.update({"date_start": start_date, "date_end": end_date})
    else:
        params["date"] = start_date
    url = settings.ZOHO_INVENTORY_SALESORDERS_URL

    session = _session_with_retry()
    items = []
    while True:
        r = zoho_get(session, url, headers, params)
        r.raise_for_status()
        js = r.json()
        items.extend(js.get("salesorders", []))
        if not js.get("page_context", {}).get("has_more_page", False):
            break
        params["page"] += 1
        time.sleep(float(os.getenv("ZOHO_PAGE_SLEEP", "0.25")))

    def fetch_one(it):
        u = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}/{it["salesorder_id"]}'
        rr = zoho_get(session, u, headers, {})
        rr.raise_for_status()
        return rr.json().get("salesorder", None)

    max_workers = int(os.getenv("ZOHO_MAX_WORKERS", "2"))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        details = [f.result() for f in as_completed([ex.submit(fetch_one, it) for it in items]) if f.result()]

    ids = [d["salesorder_id"] for d in details]
    exists = ZohoInventoryShipmentSalesOrder.objects.filter(salesorder_id__in=ids)
    existing_ids = set(exists.values_list("salesorder_id", flat=True))

    new_objs, upd = [], []
    for data in details:
        obj = create_inventory_sales_order_instance(None, data)
        if obj.salesorder_id in existing_ids:
            upd.append(obj)
        else:
            new_objs.append(obj)

    changed = False
    with transaction.atomic():
        if new_objs:
            ZohoInventoryShipmentSalesOrder.objects.bulk_create(new_objs, ignore_conflicts=True, batch_size=200)
            changed = True
        if upd:
            ZohoInventoryShipmentSalesOrder.objects.bulk_update(
                upd,
                fields=[
                    "salesorder_number","date","status","customer_id","customer_name","is_taxable","tax_id",
                    "tax_name","tax_percentage","currency_id","currency_code","currency_symbol","exchange_rate",
                    "delivery_method","total_quantity","sub_total","tax_total","total","created_by_email",
                    "created_by_name","salesperson_id","salesperson_name","is_test_order","notes","payment_terms",
                    "payment_terms_label","line_items","shipping_address","billing_address","warehouses",
                    "custom_fields","order_sub_statuses","shipment_sub_statuses","created_time","last_modified_time"
                ],
                batch_size=200
            )
    if username and changed:
        create_notification('zoho_sales_orders', 'has loaded new info from Zoho Sales Orders', 'load', username)
    return {"changed": changed, "max_ts": None}

@retry(retry=retry_if_exception_type(requests.exceptions.RequestException),
       wait=wait_exponential(multiplier=1, min=4, max=60),
       stop=stop_after_attempt(5))
def _fetch_package(package_id, session, headers):
    u = f'{settings.ZOHO_INVENTORY_PACKAGES_URL}/{package_id}'
    r = zoho_get(session, u, headers, {})
    if r.status_code == 429:
        time.sleep(10)
    r.raise_for_status()
    js = r.json()
    return js.get("package", None)

@retry(retry=retry_if_exception_type(requests.exceptions.RequestException),
       wait=wait_exponential(multiplier=1, min=4, max=60),
       stop=stop_after_attempt(5))
def _fetch_shipment_detail(it, session, headers):
    u = f'{settings.ZOHO_INVENTORY_SHIPMENTS_URL}/{it["shipment_id"]}'
    r = zoho_get(session, u, headers, {})
    if r.status_code == 429:
        time.sleep(10)
    r.raise_for_status()
    js = r.json()
    return js.get("shipmentorder", None)

def sync_inventory_shipments(*, start_date: str | None, end_date: str | None, username=None, updated_since=None):
    app_config = AppConfig.objects.first()
    headers = config_headers()
    params = {"organization_id": app_config.zoho_org_id, "per_page": 200, "page": 1}
    if end_date and start_date:
        params.update({"date_start": start_date, "date_end": end_date})
    elif start_date:
        params["date"] = start_date
    url = settings.ZOHO_INVENTORY_SHIPMENTS_URL

    session = _session_with_retry()
    items = []
    pages_fetched = 0
    while True:
        if pages_fetched >= ZOHO_MAX_PAGES_PER_RUN:
            break
        r = zoho_get(session, url, headers, params)
        if r.status_code >= 400:
            _raise_if_rate_limited(r)
            raise requests.RequestException(r.text)
        js = r.json()
        page_items = js.get("shipmentorders", [])
        if updated_since:
            trimmed, stop = [], False
            for it in page_items:
                ts = _iso_to_aware(it.get("last_modified_time") or it.get("created_time"))
                if ts and ts <= updated_since:
                    stop = True
                    break
                trimmed.append(it)
            items.extend(trimmed)
            if stop:
                break
        else:
            items.extend(page_items)
        if not js.get("page_context", {}).get("has_more_page", False):
            break
        params["page"] += 1
        pages_fetched += 1
        time.sleep(float(os.getenv("ZOHO_PAGE_SLEEP", "0.25")))

    max_workers = int(os.getenv("ZOHO_MAX_WORKERS", "2"))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        details = [f.result() for f in as_completed([ex.submit(_fetch_shipment_detail, it, session, headers) for it in items]) if f.result()]

    all_pkg_ids = []
    for d in details:
        pkg = d.get("packages", [])
        if pkg:
            all_pkg_ids.extend([p.get("package_id") for p in pkg if p.get("package_id")])
    all_pkg_ids = list(set(all_pkg_ids))

    existing_packages = ZohoPackage.objects.filter(package_id__in=all_pkg_ids)
    existing_packages_ids = set(existing_packages.values_list("package_id", flat=True))

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        pkgs_full = []
        for f in as_completed([ex.submit(_fetch_package, pid, session, headers) for pid in all_pkg_ids]):
            v = f.result()
            if v:
                pkgs_full.append(v)

    new_packages, upd_packages = [], []
    for p in pkgs_full:
        obj = create_inventory_package_instance(None, p)
        if obj.package_id in existing_packages_ids:
            upd_packages.append(obj)
        else:
            new_packages.append(obj)

    ship_ids = [d["shipment_id"] for d in details if d.get("shipment_id")]
    existing_shipments = ZohoShipmentOrder.objects.filter(shipment_id__in=ship_ids)
    existing_shipments_ids = set(existing_shipments.values_list("shipment_id", flat=True))

    new_shipments, upd_shipments = [], []
    for d in details:
        obj = create_inventory_shipment_instance(None, d)
        if obj.shipment_id in existing_shipments_ids:
            upd_shipments.append(obj)
        else:
            new_shipments.append(obj)

    shipment_fields = [
        "salesorder_id","salesorder_number","salesorder_date","salesorder_fulfilment_status","sales_channel",
        "sales_channel_formatted","shipment_number","date","shipment_status","shipment_sub_status","status",
        "detailed_status","status_message","carrier","tracking_carrier_code","service","delivery_days","source_id",
        "label_format","source_name","delivery_guarantee","reference_number","customer_id","customer_name","is_taxable",
        "tax_id","tax_name","tax_percentage","currency_id","currency_code","currency_symbol","exchange_rate","discount",
        "is_discount_before_tax","discount_type","estimate_id","delivery_method","delivery_method_id","tracking_number",
        "tracking_link","last_tracking_update_date","expected_delivery_date","shipment_delivered_date","shipment_type",
        "is_carrier_shipment","is_tracking_enabled","is_forms_available","is_email_notification_enabled","shipping_charge",
        "sub_total","tax_total","total","price_precision","is_emailed","notes","template_id","template_name",
        "template_type","created_time","last_modified_time","associated_packages_count","created_by_id",
        "last_modified_by_id","contact_persons","invoices","line_items","packages","billing_address","shipping_address",
        "custom_fields","custom_field_hash","documents","taxes","tracking_statuses","multipiece_shipments"
    ]

    package_fields = [
        "salesorder_id","salesorder_number","salesorder_date","sales_channel","sales_channel_formatted",
        "salesorder_fulfilment_status","shipment_id","shipment_number","shipment_order","package_number","date",
        "shipping_date","delivery_method","delivery_method_id","tracking_number","tracking_link","expected_delivery_date",
        "shipment_delivered_date","status","detailed_status","status_message","carrier","service","delivery_days",
        "delivery_guarantee","total_quantity","customer_id","customer_name","email","phone","mobile","contact_persons",
        "created_by_id","last_modified_by_id","created_time","last_modified_time","notes","terms","is_emailed",
        "is_advanced_tracking_missing","line_items","custom_fields","custom_field_hash","shipmentorder_custom_fields",
        "billing_address","shipping_address","picklists","template_id","template_name","template_type"
    ]

    changed = False
    max_ts = None
    for d in details:
        ts = _iso_to_aware(d.get("last_modified_time") or d.get("created_time"))
        if ts and (max_ts is None or ts > max_ts):
            max_ts = ts

    with transaction.atomic():
        if new_shipments:
            ZohoShipmentOrder.objects.bulk_create(new_shipments, ignore_conflicts=True, batch_size=200)
            changed = True
        if upd_shipments:
            ZohoShipmentOrder.objects.bulk_update(upd_shipments, fields=shipment_fields, batch_size=200)
            changed = True
        if new_packages:
            ZohoPackage.objects.bulk_create(new_packages, ignore_conflicts=True, batch_size=200)
            changed = True
        if upd_packages:
            ZohoPackage.objects.bulk_update(upd_packages, fields=package_fields, batch_size=200)
            changed = True
        JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
        JobsUpdatingTimes.objects.create(last_updated=timezone.now())
        
    if username and changed:
        create_notification('zoho_shipment', 'has loaded new info from Zoho Shipments', 'load', username)

    return {"changed": changed, "max_ts": max_ts}

def get_access_token(client_id, client_secret, refresh_token):
    cached = cache.get(ZOHO_TOKEN_KEY)
    if cached:
        return cached

    # single-flight: evita que varios workers pidan token a la vez
    got_lock = cache.add(ZOHO_TOKEN_LOCK, True, timeout=10)
    if not got_lock:
        for _ in range(20):
            tok = cache.get(ZOHO_TOKEN_KEY)
            if tok:
                return tok
            time.sleep(0.25)
        raise Exception("Timeout waiting for token from another worker")

    try:
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        if not refresh_token:
            raise Exception("Refresh token is missing")
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = requests.post(token_url, data=payload, timeout=15)
        if response.status_code != 200:
            raise Exception("Error retrieving access token")
        data = response.json()
        access_token = data["access_token"]
        # Zoho suele dar expires_in ~3600; guardamos con margen
        ttl = max(60, int(data.get("expires_in", 3600)) - 60)
        cache.set(ZOHO_TOKEN_KEY, access_token, timeout=ttl)
        return access_token
    finally:
        cache.delete(ZOHO_TOKEN_LOCK)


def refresh_zoho_access_token():
    # al refrescar, también actualiza cache
    app_config = AppConfig.objects.first()
    refresh_url = "https://accounts.zoho.com/oauth/v2/token"
    payload = {
        'refresh_token': app_config.zoho_refresh_token,
        'client_id': app_config.zoho_client_id,
        'client_secret': app_config.zoho_client_secret,
        'grant_type': 'refresh_token'
    }
    response = requests.post(refresh_url, data=payload, timeout=15)
    if response.status_code == 200:
        data = response.json()
        new_token = data.get('access_token')
        ttl = max(60, int(data.get("expires_in", 3600)) - 60)
        cache.set(ZOHO_TOKEN_KEY, new_token, timeout=ttl)
        return new_token
    raise Exception("Failed to refresh Zoho token")


def config_headers():
    app_config = AppConfig.objects.first()
    access_token = get_access_token(
        app_config.zoho_client_id,
        app_config.zoho_client_secret,
        app_config.zoho_refresh_token,
    )
    return {"Authorization": f"Zoho-oauthtoken {access_token}"}
