# services_from_main_load.py

import os

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Count


from .models import (
    ZohoInventoryItem,
    ZohoInventoryShipmentSalesOrder,
    ZohoShipmentOrder,
    ZohoPackage,
    JobsUpdatingTimes,
)
from api_senitron.models import SenitronItem, TimelineItem
from .manage_instances import (
    create_inventory_item_instance,
    create_inventory_sales_order_instance,
    create_inventory_shipment_instance,
    create_inventory_package_instance,
)

from utils.rest_utils import (
    _session_with_retry,
    _iso_to_aware,
    _sanitize_datetime_strings_inplace,
    _ensure_date_str,
    dedupe_model_instances,
    upsert_on_conflict,
    run_with_deadlock_retry,
)

from api_senitron.views import create_notification

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 60)

def set_auth_headers(headers):
    token = getattr(settings, "MAIN_LOAD_BEARER_TOKEN", None)
    if token and 'Authorization' not in headers:
        headers['Authorization'] = f"Token {token}"
    logger.info(f"Using headers for API call: {headers}")
    return headers

def api_get(session, url, params=None, headers=None, timeout=None):
    headers = set_auth_headers(headers or {})
    resp = session.get(url, params=params, headers=headers, timeout=timeout or REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp

def api_post(session, url, json=None, data=None, params=None, headers=None, timeout=None):
    """
    POST real: body en JSON (o data), opcional params si el endpoint lo requiere.
    """
    headers = set_auth_headers(headers or {})
    resp = session.post(
        url,
        params=params,
        json=json,
        data=data,
        headers=headers,
        timeout=timeout or REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp

# =========================================================
#                        ITEMS (LISTA COMPLETA)
# =========================================================


def sync_inventory_items(*, start_date: str | None = None, end_date: str | None = None, username=None):
    base_url = getattr(settings, "MAIN_LOAD_API_ITEMS_URL", settings.MAIN_LOAD_ZOHO_INVENTORY_ITEMS_URL)
    session = _session_with_retry()

    sd = _ensure_date_str(start_date)
    ed = _ensure_date_str(end_date)

    base_params = {}
    if sd:
        base_params["start_last_modified_time"] = sd
    if ed:
        base_params["end_last_modified_time"] = ed

    logger.info(f"SYNC ITEMS PARAMS: {base_params}")

    all_items = []
    page = 1
    while True:
        params = {**base_params, "page": page, "page_size": 200}
        r = api_get(session, base_url, params=params)
        data = r.json()

        page_items = data.get("items") or data.get("results") or data.get("data") or []
        if not isinstance(page_items, list):
            page_items = []

        logger.info(f"  -> page {page}: fetched {len(page_items)} items (count={data.get('count')})")
        all_items.extend(page_items)

        next_url = data.get("next")
        if not next_url:
            break

        page += 1

    logger.info(f"TOTAL fetched {len(all_items)} items from API")
    items = all_items

    # ====== IDs del API ======
    item_ids = [it.get("item_id") or it.get("id") for it in items if (it.get("item_id") or it.get("id"))]

    existing_qs = ZohoInventoryItem.objects.filter(item_id__in=item_ids)

    # ✅ FIX: dedupe en BD si hay duplicados por item_id
    dup_keys = (
        existing_qs.values("item_id")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )

    if dup_keys.exists():
        logger.warning(f"Found duplicated ZohoInventoryItem rows for {dup_keys.count()} item_id(s). Deduplicating...")

        with transaction.atomic():
            for row in dup_keys:
                inum = row["item_id"]
                qs = ZohoInventoryItem.objects.filter(item_id=inum).order_by("-id")

                keep = qs.first()
                qs.exclude(id=keep.id).delete()

    # Re-consulta limpio para construir el mapa seguro
    existing_qs = ZohoInventoryItem.objects.filter(item_id__in=item_ids)
    existing_map = {it.item_id: it for it in existing_qs}

    timelines = []
    changed = False
    max_ts = None

    to_create: list[ZohoInventoryItem] = []
    to_update: list[ZohoInventoryItem] = []
    seen_new_ids = set()

    for data_item in items:
        _sanitize_datetime_strings_inplace(data_item)

        new_obj = create_inventory_item_instance(None, data_item)

        # ⚠️ Nota: aquí estás usando item_id como item_number en Senitron (revísalo)
        senitron_item = SenitronItem.objects.filter(item_number=new_obj.item_id).first()

        lm = _iso_to_aware(
            getattr(new_obj, "last_modified_time", None)
            or getattr(new_obj, "created_time", None)
        )
        if lm and (max_ts is None or lm > max_ts):
            max_ts = lm

        prev = existing_map.get(new_obj.item_id)

        if prev:
            # ==== Timelines ====
            if getattr(prev, "status", None) != getattr(new_obj, "status", None):
                timelines.append(
                    TimelineItem(
                        item_number=new_obj.item_id,
                        previous_status_zoho=prev.status,
                        date_previous_status_zoho=prev.last_modified_time or prev.created_time,
                        actual_status_zoho=new_obj.status,
                        date_actual_status_zoho=new_obj.last_modified_time or new_obj.created_time,
                        zoho_item=prev,
                        senitron_item=senitron_item,
                        text=f"{getattr(new_obj, 'sku', None) or '-'} status changed -> From {prev.status} to {new_obj.status}",
                    )
                )

            try:
                if int(prev.stock_on_hand) != int(new_obj.stock_on_hand):
                    ch = "added" if new_obj.stock_on_hand > prev.stock_on_hand else "removed"
                    absv = abs(new_obj.stock_on_hand - prev.stock_on_hand)
                    timelines.append(
                        TimelineItem(
                            item_number=new_obj.item_id,
                            previous_stock_on_hand=prev.stock_on_hand,
                            date_previous_stock_on_hand=prev.last_modified_time or prev.created_time,
                            actual_stock_on_hand=new_obj.stock_on_hand,
                            date_actual_stock_on_hand=new_obj.last_modified_time or new_obj.created_time,
                            zoho_item=prev,
                            senitron_item=senitron_item,
                            text=f"{getattr(new_obj, 'sku', None) or '-'} : {int(absv)} unit(s) {ch} -> New stock on hand: {int(new_obj.stock_on_hand)}",
                        )
                    )
            except Exception:
                pass

            # ==== sync fields ====
            prev.status = new_obj.status
            prev.stock_on_hand = new_obj.stock_on_hand
            prev.last_modified_time = new_obj.last_modified_time

            to_update.append(prev)

        else:
            # Nuevo item
            if new_obj.item_id in seen_new_ids:
                logger.debug(f"Duplicate new item_id in same batch, skipping: {new_obj.item_id}")
                continue

            timelines.append(
                TimelineItem(
                    item_number=new_obj.item_id,
                    actual_stock_on_hand=new_obj.stock_on_hand,
                    date_actual_stock_on_hand=new_obj.last_modified_time or new_obj.created_time,
                    actual_status_zoho=new_obj.status,
                    date_actual_status_zoho=new_obj.last_modified_time or new_obj.created_time,
                    zoho_item=new_obj,
                    senitron_item=senitron_item,
                    text=f"{getattr(new_obj, 'sku', None) or '-'} created -> On hand: {int(getattr(new_obj, 'stock_on_hand', 0))}, Status: {getattr(new_obj, 'status', '-')}",
                )
            )

            to_create.append(new_obj)
            seen_new_ids.add(new_obj.item_id)

    def _write_items():
        nonlocal changed

        if to_create:
            # ✅ Recomendación: si no tienes UNIQUE en DB, no uses ignore_conflicts
            ZohoInventoryItem.objects.bulk_create(
                to_create,
                batch_size=int(os.getenv("API_BATCH_SIZE_ITEMS", "500")),
            )
            changed = True

        if to_update:
            ZohoInventoryItem.objects.bulk_update(
                to_update,
                ["status", "stock_on_hand", "last_modified_time"],
                batch_size=int(os.getenv("API_BATCH_SIZE_ITEMS", "500")),
            )
            changed = True

        if timelines:
            TimelineItem.objects.bulk_create(
                timelines,
                batch_size=int(os.getenv("API_BATCH_SIZE_TIMELINES", "200")),
                ignore_conflicts=True,
            )

        JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
        JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    run_with_deadlock_retry(_write_items)

    if username and changed:
        create_notification("items", "loaded new info from API Items", "load", username)

    return {"changed": changed, "max_ts": max_ts}

# def sync_inventory_items(*, start_date: str | None = None, end_date: str | None = None, username=None):
#     base_url = getattr(settings, "MAIN_LOAD_API_ITEMS_URL", settings.MAIN_LOAD_ZOHO_INVENTORY_ITEMS_URL)
#     session = _session_with_retry()

#     sd = _ensure_date_str(start_date)
#     ed = _ensure_date_str(end_date)

#     base_params = {}
#     if sd:
#         base_params["start_last_modified_time"] = sd
#     if ed:
#         base_params["end_last_modified_time"] = ed

#     logger.info(f"SYNC ITEMS PARAMS: {base_params}")
    
#     all_items = []
#     page = 1
#     while True:
#         params = {**base_params, "page": page, "page_size": 200}
#         r = api_get(session, base_url, params=params)
#         data = r.json()

#         page_items = data.get("items") or data.get("results") or data.get("data") or []
#         if not isinstance(page_items, list):
#             page_items = []

#         logger.info(f"  -> page {page}: fetched {len(page_items)} items (count={data.get('count')})")
#         all_items.extend(page_items)
        
#         next_url = data.get("next")
#         if not next_url:
#             break

#         page += 1

#     logger.info(f"TOTAL fetched {len(all_items)} items from API")
#     items = all_items

#     item_ids = [it.get("item_id") or it.get("id") for it in items if (it.get("item_id") or it.get("id"))]
#     existing_qs = ZohoInventoryItem.objects.filter(item_id__in=item_ids)
#     existing_map = {it.item_id: it for it in existing_qs}

#     timelines = []
#     changed = False
#     max_ts = None

#     to_create: list[ZohoInventoryItem] = []
#     to_update: list[ZohoInventoryItem] = []
#     seen_new_ids = set()

#     for data_item in items:
#         _sanitize_datetime_strings_inplace(data_item)

#         # Creamos un "nuevo" objeto con los datos que vienen del API
#         new_obj = create_inventory_item_instance(None, data_item)
#         senitron_item = SenitronItem.objects.filter(item_number=new_obj.item_id).first()

#         lm = _iso_to_aware(
#             getattr(new_obj, "last_modified_time", None)
#             or getattr(new_obj, "created_time", None)
#         )
#         if lm and (max_ts is None or lm > max_ts):
#             max_ts = lm

#         prev = existing_map.get(new_obj.item_id)

#         if prev:
#             # ==== Timelines ====
#             if getattr(prev, "status", None) != getattr(new_obj, "status", None):
#                 timelines.append(
#                     TimelineItem(
#                         item_number=new_obj.item_id,
#                         previous_status_zoho=prev.status,
#                         date_previous_status_zoho=prev.last_modified_time or prev.created_time,
#                         actual_status_zoho=new_obj.status,
#                         date_actual_status_zoho=new_obj.last_modified_time or new_obj.created_time,
#                         zoho_item=prev,   # referenciamos el existente
#                         senitron_item=senitron_item,
#                         text=f"{getattr(new_obj, 'sku', None) or '-'} status changed -> From {prev.status} to {new_obj.status}",
#                     )
#                 )
#             try:
#                 if int(prev.stock_on_hand) != int(new_obj.stock_on_hand):
#                     ch = "added" if new_obj.stock_on_hand > prev.stock_on_hand else "removed"
#                     absv = abs(new_obj.stock_on_hand - prev.stock_on_hand)
#                     timelines.append(
#                         TimelineItem(
#                             item_number=new_obj.item_id,
#                             previous_stock_on_hand=prev.stock_on_hand,
#                             date_previous_stock_on_hand=prev.last_modified_time or prev.created_time,
#                             actual_stock_on_hand=new_obj.stock_on_hand,
#                             date_actual_stock_on_hand=new_obj.last_modified_time or new_obj.created_time,
#                             zoho_item=prev,
#                             senitron_item=senitron_item,
#                             text=f"{getattr(new_obj, 'sku', None) or '-'} : {int(absv)} unit(s) {ch} -> New stock on hand: {int(new_obj.stock_on_hand)}",
#                         )
#                     )
#             except Exception:
#                 pass

#             # ==== Actualizamos el objeto existente con los nuevos valores ====
#             # aquí puedes copiar más campos si quieres mantener todo sincronizado:
#             prev.status = new_obj.status
#             prev.stock_on_hand = new_obj.stock_on_hand
#             prev.last_modified_time = new_obj.last_modified_time
#             # prev.sku = new_obj.sku
#             # prev.name = new_obj.name
#             # ...

#             to_update.append(prev)
#         else:
#             # Nuevo item
#             if new_obj.item_id in seen_new_ids:
#             # opcional: log para debug
#                 logger.debug(f"Duplicate new item_id in same batch, skipping: {new_obj.item_id}")
#                 continue
#             timelines.append(
#                 TimelineItem(
#                     item_number=new_obj.item_id,
#                     actual_stock_on_hand=new_obj.stock_on_hand,
#                     date_actual_stock_on_hand=new_obj.last_modified_time or new_obj.created_time,
#                     actual_status_zoho=new_obj.status,
#                     date_actual_status_zoho=new_obj.last_modified_time or new_obj.created_time,
#                     zoho_item=new_obj,
#                     senitron_item=senitron_item,
#                     text=f"{getattr(new_obj, 'sku', None) or '-'} created -> On hand: {int(getattr(new_obj, 'stock_on_hand', 0))}, Status: {getattr(new_obj, 'status', '-')}",
#                 )
#             )
#             to_create.append(new_obj)
#             seen_new_ids.add(new_obj.item_id)

#     def _write_items():
#         nonlocal changed

#         if to_create:
#             ZohoInventoryItem.objects.bulk_create(
#                 to_create,
#                 batch_size=int(os.getenv("API_BATCH_SIZE_ITEMS", "500")),
#                 ignore_conflicts=True,
#             )
#             changed = True

#         if to_update:
#             ZohoInventoryItem.objects.bulk_update(
#                 to_update,
#                 ["status", "stock_on_hand", "last_modified_time"],
#                 batch_size=int(os.getenv("API_BATCH_SIZE_ITEMS", "500")),
#             )
#             changed = True

#         if timelines:
#             TimelineItem.objects.bulk_create(
#                 timelines,
#                 batch_size=int(os.getenv("API_BATCH_SIZE_TIMELINES", "200")),
#                 ignore_conflicts=True,
#             )

#         JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
#         JobsUpdatingTimes.objects.create(last_updated=timezone.now())

#     run_with_deadlock_retry(_write_items)

#     if username and changed:
#         create_notification("items", "loaded new info from API Items", "load", username)

#     return {"changed": changed, "max_ts": max_ts}


# =========================================================
#               SALES ORDERS (LISTA COMPLETA)
# =========================================================

def sync_inventory_sales_orders(*, start_date: str, end_date: str | None = None, username=None):
    url = getattr(settings, "MAIN_LOAD_API_SALESORDERS_URL", settings.MAIN_LOAD_ZOHO_INVENTORY_SALESORDERS_URL)
    session = _session_with_retry()

    sd = _ensure_date_str(start_date)
    ed = _ensure_date_str(end_date)

    params = {"start_date": sd}
    if ed:
        params["end_date"] = ed
        
    all_items = []
    page = 1
    while True:
        params = {**params, "page": page, "page_size": 200}
        r = api_get(session, url, params=params)
        data = r.json()

        page_items = data.get("salesorders") or data.get("results") or data.get("data") or []
        if not isinstance(page_items, list):
            page_items = []

        logger.info(f"  -> page {page}: fetched {len(page_items)} salesorders (count={data.get('count')})")
        all_items.extend(page_items)
        
        next_url = data.get("next")
        if not next_url:
            break

        page += 1

    logger.info(f"TOTAL fetched {len(all_items)} salesorders from API")
    items = all_items

    objs_to_upsert = []
    for it in items:
        _sanitize_datetime_strings_inplace(it)  # solo zona; no recorte
        obj = create_inventory_sales_order_instance(None, it)
        objs_to_upsert.append(obj)

    changed = False

    def _write_sales_orders():
        nonlocal changed
        n = upsert_on_conflict(
            ZohoInventoryShipmentSalesOrder,
            objs_to_upsert,
            unique_fields=["salesorder_id"],
            update_fields=[
                "salesorder_number","date","status","customer_id","customer_name","is_taxable","tax_id",
                "tax_name","tax_percentage","currency_id","currency_code","currency_symbol","exchange_rate",
                "delivery_method","total_quantity","sub_total","tax_total","total","created_by_email",
                "created_by_name","salesperson_id","salesperson_name","is_test_order","notes","payment_terms",
                "payment_terms_label","line_items","shipping_address","billing_address","warehouses",
                "custom_fields","order_sub_statuses","shipment_sub_statuses","created_time","last_modified_time"
            ],
            batch_size=int(os.getenv("API_BATCH_SIZE_SALESORDERS", "100")),
        )
        if n:
            changed = True

        JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
        JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    run_with_deadlock_retry(_write_sales_orders)

    if username and changed:
        create_notification("sales_orders", "loaded new info from API Sales Orders", "load", username)

    return {"changed": changed, "max_ts": None}

# =========================================================
#    SHIPMENTS (LISTA COMPLETA) + PACKAGES BULK POR IDs
# =========================================================


def _chunk_by_max_url(ids: list[str], base_url: str, param_name: str = "shipment_ids", max_url_len: int = 7000):
    """
    Crea chunks que no excedan un tamaño razonable de URL.
    max_url_len=7000 suele ser seguro detrás de proxies (evita 414).
    """
    # Longitud aproximada de: base_url + "?shipment_ids=" + csv
    prefix_len = len(base_url) + 1 + len(param_name) + 1  # ? + param + =
    chunks = []
    current = []
    current_len = prefix_len

    for _id in ids:
        s = str(_id).strip()
        if not s:
            continue
        add_len = len(s) + (1 if current else 0)  # coma si no es el primero

        if current and (current_len + add_len) > max_url_len:
            chunks.append(current)
            current = [s]
            current_len = prefix_len + len(s)
        else:
            current.append(s)
            current_len += add_len

    if current:
        chunks.append(current)

    return chunks


def _fetch_packages_bulk_by_shipments(session, url_packages: str, shipment_ids) -> list[dict]:
    """
    MANTIENE GET (porque main-load-data no permite POST -> 405)
    pero evita 414 haciendo múltiples GET en chunks.
    """
    if not shipment_ids:
        return []

    # Normaliza a lista
    if isinstance(shipment_ids, (list, tuple, set)):
        ids = [str(s).strip() for s in shipment_ids if s]
    else:
        ids = [s.strip() for s in str(shipment_ids).split(",") if s.strip()]

    # dedupe preservando orden
    ids = list(dict.fromkeys(ids))
    if not ids:
        return []

    all_pkgs: list[dict] = []

    # Divide por tamaño de URL
    chunks = _chunk_by_max_url(ids, base_url=url_packages, param_name="shipment_ids", max_url_len=7000)

    for chunk in chunks:
        shipment_ids_csv = ",".join(chunk)
        params = {"shipment_ids": shipment_ids_csv}

        rp = api_get(session, url_packages, params=params)  # ✅ GET como exige main-load-data
        body = rp.json()
        pkgs = body.get("packages") or body.get("results") or body.get("data") or []
        if isinstance(pkgs, list) and pkgs:
            all_pkgs.extend(pkgs)

    return all_pkgs

def sync_inventory_shipments(*, start_date: str | None, end_date: str | None, username=None, updated_since=None):
    url_ship = getattr(settings, "MAIN_LOAD_API_SHIPMENTS_URL", settings.MAIN_LOAD_ZOHO_INVENTORY_SHIPMENTS_URL)
    url_pkg = getattr(settings, "MAIN_LOAD_API_PACKAGES_URL", settings.MAIN_LOAD_ZOHO_INVENTORY_PACKAGES_URL)

    session = _session_with_retry()

    sd = _ensure_date_str(start_date) if start_date else None
    ed = _ensure_date_str(end_date) if end_date else None

    params = {}
    if sd:
        params["start_last_modified_time"] = sd
    if ed:
        params["end_last_modified_time"] = ed

    logger.info(f"SYNC SHIPMENTS PARAMS: {params}")

    all_items = []
    page = 1
    while True:
        params = {**params, "page": page, "page_size": 200}
        r = api_get(session, url_ship, params=params)
        data = r.json()

        page_items = data.get("shipmentorders") or data.get("results") or data.get("data") or []
        if not isinstance(page_items, list):
            page_items = []

        logger.info(f"  -> page {page}: fetched {len(page_items)} shipmentorders (count={data.get('count')})")
        all_items.extend(page_items)
        
        next_url = data.get("next")
        if not next_url:
            break

        page += 1

    logger.info(f"TOTAL fetched {len(all_items)} shipmentorders from API")
    items = all_items

    # 2) Filtrado adicional por updated_since (si lo usas)
    # if updated_since:
    #     filtered = []
    #     for it in items:
    #         ts = _iso_to_aware(it.get("last_modified_time") or it.get("created_time"))
    #         if not ts or ts > updated_since:
    #             filtered.append(it)
    #     items = filtered

    details = items[:]  # ya vienen detallados
    for d in details:
        _sanitize_datetime_strings_inplace(d)  # solo zona; no recorte

    # 3) Packages en bulk por shipment_ids
    shipment_ids = [d.get("shipment_id") for d in details if d.get("shipment_id")]
    pkgs_full = _fetch_packages_bulk_by_shipments(session, url_pkg, shipment_ids)
    
    for p in pkgs_full:
        _sanitize_datetime_strings_inplace(p)

    # 4) Preparar objetos
    ship_objs = [create_inventory_shipment_instance(None, d) for d in details]
    pkg_objs = [create_inventory_package_instance(None, p) for p in pkgs_full]

    ship_objs = dedupe_model_instances(logger, ship_objs, key_attr="shipment_id", newer_wins=True)
    pkg_objs  = dedupe_model_instances(logger, pkg_objs,  key_attr="package_id",  newer_wins=True)
    
    logger.info(f"  -> prepared {len(ship_objs)} unique shipment objects to upsert")
    logger.info(f"  -> prepared {len(pkg_objs)} unique package objects to upsert")

    # 5) UPSERTS
    changed = False
    max_ts = None
    for d in details:
        ts = _iso_to_aware(d.get("last_modified_time") or d.get("created_time"))
        if ts and (max_ts is None or ts > max_ts):
            max_ts = ts

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

    def _write_shipments_packages():
        nonlocal changed
        n1 = upsert_on_conflict(
            ZohoShipmentOrder,
            ship_objs,
            unique_fields=["shipment_id"],
            update_fields=shipment_fields,
            batch_size=int(os.getenv("API_BATCH_SIZE_SHIPMENTS", "100")),
        )
        if n1:
            changed = True

        if pkg_objs:
            n2 = upsert_on_conflict(
                ZohoPackage,
                pkg_objs,
                unique_fields=["package_id"],
                update_fields=package_fields,
                batch_size=int(os.getenv("API_BATCH_SIZE_PACKAGES", "100")),
            )
            if n2:
                changed = True

        JobsUpdatingTimes.objects.filter(last_updated__lt=timezone.now()).delete()
        JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    run_with_deadlock_retry(_write_shipments_packages)

    if username and changed:
        create_notification("shipments", "loaded new info from API Shipments & Packages", "load", username)

    return {"changed": changed, "max_ts": max_ts}
