# manage_instances.py (create instances)

from datetime import datetime as dt, date as date_cls
from django.utils import timezone
from django.db.utils import IntegrityError
from .models import (
    ZohoInventoryItem,
    ZohoInventoryShipmentSalesOrder,
    ZohoShipmentOrder,
    ZohoPackage,
    ZohoItemAssetsTrack,
)
from django.db import transaction

from api_zoho.models import ZohoInventoryItem
from api_senitron.models import TimelineItem  # ajusta si está en otro app


import re

# -------------------------
# Helpers de parseo flexibles
# -------------------------

_ISO_NO_TZ_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$')

def _log(logger, level, msg):
    try:
        if logger:
            getattr(logger, level, None) and getattr(logger, level)(msg)
    except Exception:
        pass

def _ensure_iso_with_tz(s: str) -> str:
    """
    Si llega ISO con 'T' pero sin zona, asume UTC (+00:00).
    Si trae 'Z', lo convierte a '+00:00' por uniformidad.
    No recorta contenido.
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
        return t  # ya tiene offset
    if _ISO_NO_TZ_RE.match(t):
        return t + '+00:00'
    if '+' not in t and '-' not in t[-6:] and not t.endswith('+00:00'):
        return t + '+00:00'
    return t

def _parse_dt_any(v, logger=None):
    """
    Devuelve datetime aware (timezone actual).
    - v puede ser str / datetime / date / None
    - Strings ISO con 'T' sin zona → +00:00 (UTC) antes de parsear
    - Datetimes naive → se localizan a la tz actual
    """
    if v is None:
        return None

    tz = timezone.get_current_timezone()

    if isinstance(v, dt):
        return v if v.tzinfo else tz.localize(v)

    if isinstance(v, date_cls):
        # subirlo a datetime a medianoche de ese día (aware)
        return tz.localize(dt.combine(v, dt.min.time()))

    if isinstance(v, str):
        try:
            vv = _ensure_iso_with_tz(v) if 'T' in v else v
            # dt.fromisoformat acepta 'YYYY-MM-DD' y 'YYYY-MM-DDTHH:MM:SS[.fff][±HH:MM]'
            parsed = dt.fromisoformat(vv)
            if parsed.tzinfo:
                # Convertimos a tz actual para consistencia con tu código previo
                return parsed.astimezone(tz)
            return tz.localize(parsed)
        except Exception:
            # Compatibilidad: intenta formatos comunes
            for fmt in ('%Y-%m-%dT%H:%M:%S%z',
                        '%Y-%m-%d %H:%M:%S%z',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d'):
                try:
                    parsed = dt.strptime(v, fmt)
                    if fmt.endswith('%z'):
                        return parsed.astimezone(tz)
                    return tz.localize(parsed)
                except Exception:
                    continue
            _log(logger, 'error', f"Could not parse datetime: {v}")
            return None

    _log(logger, 'error', f"Unsupported datetime type: {type(v)}")
    return None

def _parse_date_any(v, logger=None):
    """
    Devuelve date (no datetime).
    - v puede ser str / datetime / date / None
    - Si llega datetime (o string con T), devuelve sólo la parte de fecha.
    """
    if v is None:
        return None

    if isinstance(v, date_cls) and not isinstance(v, dt):
        return v

    if isinstance(v, dt):
        return v.date()

    if isinstance(v, str):
        try:
            if 'T' in v:
                vv = _ensure_iso_with_tz(v)
                return dt.fromisoformat(vv).date()
            # Acepta 'YYYY-MM-DD'
            return dt.fromisoformat(v[:10]).date()
        except Exception:
            for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y'):
                try:
                    return dt.strptime(v[:10], fmt).date()
                except Exception:
                    continue
            _log(logger, 'error', f"Could not parse date: {v}")
            return None

    _log(logger, 'error', f"Unsupported date type: {type(v)}")
    return None

# =========================================================
# CREATE ITEM INVENTORY INSTANCE
# =========================================================


def create_inventory_item_instance(logger, data):
    created_time = _parse_dt_any(data.get('created_time'), logger)
    last_modified_time = _parse_dt_any(data.get('last_modified_time'), logger)

    item_id = (data.get('item_id') or '').strip()
    if not item_id:
        _log(logger, 'warning', "Missing item_id. Skipping.")
        return None

    defaults = {
        'group_id': data.get('group_id', 0),
        'group_name': data.get('group_name', ''),
        'name': data.get('name', ''),
        'status': data.get('status', ''),
        'source': data.get('source', ''),
        'is_linked_with_zohocrm': data.get('is_linked_with_zohocrm', False),
        'item_type': data.get('item_type', ''),
        'description': data.get('description', ''),
        'rate': data.get('rate', 0),
        'is_taxable': data.get('is_taxable', False),
        'tax_id': data.get('tax_id') if isinstance(data.get('tax_id'), (int, float)) else 0,
        'tax_name': data.get('tax_name', ''),
        'tax_percentage': data.get('tax_percentage', 0),
        'purchase_description': data.get('purchase_description', ''),
        'purchase_rate': data.get('purchase_rate', 0),
        'is_combo_product': data.get('is_combo_product', False),
        'product_type': data.get('product_type', ''),
        'attribute_id1': data.get('attribute_id1') if isinstance(data.get('attribute_id1'), (int, float)) else 0,
        'attribute_name1': data.get('attribute_name1', ''),
        'reorder_level': data.get('reorder_level') if isinstance(data.get('reorder_level'), (int, float)) else 0,
        'stock_on_hand': data.get('stock_on_hand', 0),
        'available_stock': data.get('available_stock', 0),
        'actual_available_stock': data.get('actual_available_stock', 0),
        'sku': data.get('sku', ''),
        'upc': data.get('upc') if isinstance(data.get('upc'), (int, float)) else 0,
        'ean': data.get('ean') if isinstance(data.get('ean'), (int, float)) else 0,
        'isbn': data.get('isbn') if isinstance(data.get('isbn'), (int, float)) else 0,
        'part_number': data.get('part_number') if isinstance(data.get('part_number'), (int, float)) else 0,
        'attribute_option_id1': data.get('attribute_option_id1') if isinstance(data.get('attribute_option_id1'), (int, float)) else 0,
        'attribute_option_name1': data.get('attribute_option_name1', ''),
        'image_name': data.get('image_name', ''),
        'image_type': data.get('image_type', ''),
        'created_time': created_time,
        'last_modified_time': last_modified_time,
        'hsn_or_sac': data.get('hsn_or_sac') if isinstance(data.get('hsn_or_sac'), (int, float)) else 0,
        'sat_item_key_code': data.get('sat_item_key_code', ''),
        'unitkey_code': data.get('unitkey_code', ''),
        # 'synced_with_senitron': data.get('synced_with_senitron', False),
    }

    try:
        with transaction.atomic():
            # 🔒 lock para evitar carreras concurrentes
            qs = ZohoInventoryItem.objects.select_for_update().filter(item_id=item_id)

            obj = qs.order_by("-id").first()

            if obj:
                # ✅ si hay duplicados, reasignar timelines y borrar extras
                dup_qs = qs.exclude(id=obj.id)
                if dup_qs.exists():
                    TimelineItem.objects.filter(zoho_item__in=dup_qs).update(zoho_item=obj)
                    dup_qs.delete()

                # update fields
                for k, v in defaults.items():
                    setattr(obj, k, v)

                obj.save(update_fields=list(defaults.keys()))
                return obj

            # create si no existe
            obj = ZohoInventoryItem.objects.create(item_id=item_id, **defaults)
            return obj

    except IntegrityError as e:
        _log(logger, 'error', f"Integrity error for item_id={item_id}: {e}. Skipping.")
        return None
    except Exception as e:
        _log(logger, 'error', f"Unexpected error for item_id={item_id}: {e}")
        return None

# =========================================================
# CREATE SALES ORDER INVENTORY INSTANCE
# =========================================================

def create_inventory_sales_order_instance(logger, data):
    current_timezone = timezone.get_current_timezone()

    # 'date' es date-only en el modelo ⇒ convertir a date si viene datetime/str
    date_value = _parse_date_any(data.get('date'), logger)

    created_time = _parse_dt_any(data.get('created_time'), logger)
    last_modified_time = _parse_dt_any(data.get('last_modified_time'), logger)

    salesorder_id = data.get('salesorder_id', '')
    salesorder_number = data.get('salesorder_number', '')
    status = data.get('status', '')
    customer_id = data.get('customer_id', '')
    customer_name = data.get('customer_name', '')
    is_taxable = data.get('is_taxable', True)
    tax_id = data.get('tax_id', '')
    tax_name = data.get('tax_name', '')
    tax_percentage = data.get('tax_percentage', 0.0)
    currency_id = data.get('currency_id', '')
    currency_code = data.get('currency_code', '')
    currency_symbol = data.get('currency_symbol', '')
    exchange_rate = data.get('exchange_rate', 1.0)
    delivery_method = data.get('delivery_method', '')
    total_quantity = data.get('total_quantity', 0.0)
    sub_total = data.get('sub_total', 0.0)
    tax_total = data.get('tax_total', 0.0)
    total = data.get('total', 0.0)
    created_by_email = data.get('created_by_email', '')
    created_by_name = data.get('created_by_name', '')
    salesperson_id = data.get('salesperson_id', '')
    salesperson_name = data.get('salesperson_name', '')
    is_test_order = data.get('is_test_order', False)
    notes = data.get('notes', '')
    payment_terms = data.get('payment_terms', 0)
    payment_terms_label = data.get('payment_terms_label', '')

    # JSON Fields
    line_items = data.get('line_items', [])
    shipping_address = data.get('shipping_address', {})
    billing_address = data.get('billing_address', {})
    warehouses = data.get('warehouses', [])
    custom_fields = data.get('custom_fields', {})
    order_sub_statuses = data.get('order_sub_statuses', [])
    shipment_sub_statuses = data.get('shipment_sub_statuses', [])

    try:
        obj, _ = ZohoInventoryShipmentSalesOrder.objects.update_or_create(
            salesorder_id=salesorder_id,
            defaults={
                'salesorder_number': salesorder_number,
                'date': date_value,  # DateField
                'status': status,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'is_taxable': is_taxable,
                'tax_id': tax_id,
                'tax_name': tax_name,
                'tax_percentage': tax_percentage,
                'currency_id': currency_id,
                'currency_code': currency_code,
                'currency_symbol': currency_symbol,
                'exchange_rate': exchange_rate,
                'delivery_method': delivery_method,
                'total_quantity': total_quantity,
                'sub_total': sub_total,
                'tax_total': tax_total,
                'total': total,
                'created_by_email': created_by_email,
                'created_by_name': created_by_name,
                'salesperson_id': salesperson_id,
                'salesperson_name': salesperson_name,
                'is_test_order': is_test_order,
                'notes': notes,
                'payment_terms': payment_terms,
                'payment_terms_label': payment_terms_label,
                'line_items': line_items,
                'shipping_address': shipping_address,
                'billing_address': billing_address,
                'warehouses': warehouses,
                'custom_fields': custom_fields,
                'order_sub_statuses': order_sub_statuses,
                'shipment_sub_statuses': shipment_sub_statuses,
                'created_time': created_time,
                'last_modified_time': last_modified_time,
            }
        )
        return obj
    except IntegrityError:
        _log(logger, 'error', f"Integrity error for salesorder_id={salesorder_id}. Skipping.")
        return None

# =========================================================
# CREATE SHIPMENT INVENTORY INSTANCE
# =========================================================

def create_inventory_shipment_instance(logger, data):
    current_timezone = timezone.get_current_timezone()

    created_time = _parse_dt_any(data.get('created_time'), logger)
    last_modified_time = _parse_dt_any(data.get('last_modified_time'), logger)

    # En tu modelo usas DateTimeField para 'salesorder_date' y 'date' (según tu código original).
    # Mantengo la misma estrategia: si llega sólo fecha, la hago aware a medianoche.
    salesorder_date_raw = data.get('salesorder_date')
    date_raw = data.get('date')

    salesorder_date_dt = _parse_dt_any(salesorder_date_raw, logger)  # datetime aware (si llega date, sube a 00:00)
    date_dt = _parse_dt_any(date_raw, logger)

    shipment_id = data.get('shipment_id', '')

    try:
        obj, _ = ZohoShipmentOrder.objects.update_or_create(
            shipment_id=shipment_id,
            defaults={
                'salesorder_id': data.get('salesorder_id', ''),
                'salesorder_number': data.get('salesorder_number', ''),
                'salesorder_date': salesorder_date_dt,
                'salesorder_fulfilment_status': data.get('salesorder_fulfilment_status', ''),
                'sales_channel': data.get('sales_channel', ''),
                'sales_channel_formatted': data.get('sales_channel_formatted', ''),
                'shipment_number': data.get('shipment_number', ''),
                'date': date_dt,
                'shipment_status': data.get('shipment_status', ''),
                'shipment_sub_status': data.get('shipment_sub_status', ''),
                'status': data.get('status', ''),
                'detailed_status': data.get('detailed_status', ''),
                'status_message': data.get('status_message', ''),
                'carrier': data.get('carrier', ''),
                'tracking_carrier_code': data.get('tracking_carrier_code', ''),
                'service': data.get('service', ''),
                'delivery_days': data.get('delivery_days', ''),
                'source_id': data.get('source_id', ''),
                'label_format': data.get('label_format', ''),
                'source_name': data.get('source_name', ''),
                'delivery_guarantee': data.get('delivery_guarantee', False),
                'reference_number': data.get('reference_number', ''),
                'customer_id': data.get('customer_id', ''),
                'customer_name': data.get('customer_name', ''),
                'is_taxable': data.get('is_taxable', True),
                'tax_id': data.get('tax_id', ''),
                'tax_name': data.get('tax_name', ''),
                'tax_percentage': data.get('tax_percentage', 0),
                'currency_id': data.get('currency_id', ''),
                'currency_code': data.get('currency_code', ''),
                'currency_symbol': data.get('currency_symbol', ''),
                'exchange_rate': data.get('exchange_rate', 1),
                'discount': data.get('discount', 0),
                'is_discount_before_tax': data.get('is_discount_before_tax', False),
                'discount_type': data.get('discount_type', ''),
                'estimate_id': data.get('estimate_id', ''),
                'delivery_method': data.get('delivery_method', ''),
                'delivery_method_id': data.get('delivery_method_id', ''),
                'tracking_number': data.get('tracking_number', ''),
                'tracking_link': data.get('tracking_link', ''),
                'last_tracking_update_date': _parse_dt_any(data.get('last_tracking_update_date'), logger),
                'expected_delivery_date': _parse_dt_any(data.get('expected_delivery_date'), logger),
                'shipment_delivered_date': _parse_dt_any(data.get('shipment_delivered_date'), logger),
                'shipment_type': data.get('shipment_type', ''),
                'is_carrier_shipment': data.get('is_carrier_shipment', False),
                'is_tracking_enabled': data.get('is_tracking_enabled', False),
                'is_forms_available': data.get('is_forms_available', False),
                'is_email_notification_enabled': data.get('is_email_notification_enabled', False),
                'shipping_charge': data.get('shipping_charge', 0),
                'sub_total': data.get('sub_total', 0),
                'tax_total': data.get('tax_total', 0),
                'total': data.get('total', 0),
                'price_precision': data.get('price_precision', 0),
                'is_emailed': data.get('is_emailed', False),
                'notes': data.get('notes', ''),
                'template_id': data.get('template_id', ''),
                'template_name': data.get('template_name', ''),
                'template_type': data.get('template_type', ''),
                'created_time': created_time,
                'last_modified_time': last_modified_time,
                'associated_packages_count': data.get('associated_packages_count', 0),
                'created_by_id': data.get('created_by_id', ''),
                'last_modified_by_id': data.get('last_modified_by_id', ''),
                # Campos JSON anidados
                'contact_persons': data.get('contact_persons', []),
                'invoices': data.get('invoices', []),
                'line_items': data.get('line_items', []),
                'packages': data.get('packages', []),
                'billing_address': data.get('billing_address', {}),
                'shipping_address': data.get('shipping_address', {}),
                'custom_fields': data.get('custom_fields', []),
                'custom_field_hash': data.get('custom_field_hash', {}),
                'documents': data.get('documents', []),
                'taxes': data.get('taxes', []),
                'tracking_statuses': data.get('tracking_statuses', []),
                'multipiece_shipments': data.get('multipiece_shipments', []),
            }
        )
        return obj
    except IntegrityError:
        _log(logger, 'error', f"Integrity error for shipment_id={shipment_id}. Skipping.")
        return None
    except Exception as e:
        _log(logger, 'error', f"Error creating shipment order instance: {e}")
        return None

# =========================================================
# CREATE PACKAGE INVENTORY INSTANCE
# =========================================================

def create_inventory_package_instance(logger, data, zoho_shipment=None):
    current_timezone = timezone.get_current_timezone()

    # Estos campos son DateField en tu modelo (según tu implementación previa).
    salesorder_date = _parse_date_any(data.get('salesorder_date'), logger)
    date_value = _parse_date_any(data.get('date'), logger)
    shipping_date = _parse_date_any(data.get('shipping_date'), logger)

    created_time = _parse_dt_any(data.get('created_time'), logger) or timezone.now()
    last_modified_time = _parse_dt_any(data.get('last_modified_time'), logger) or timezone.now()

    package_id = data.get('package_id', '')

    try:
        package, _ = ZohoPackage.objects.update_or_create(
            package_id=package_id,
            defaults={
                'salesorder_id': data.get('salesorder_id', ''),
                'salesorder_number': data.get('salesorder_number', ''),
                'salesorder_date': salesorder_date,       # DateField
                'sales_channel': data.get('sales_channel', ''),
                'sales_channel_formatted': data.get('sales_channel_formatted', ''),
                'salesorder_fulfilment_status': data.get('salesorder_fulfilment_status', ''),
                'shipment_id': data.get('shipment_id', ''),
                'shipment_number': data.get('shipment_number', ''),
                'shipment_order': data.get('shipment_order', {}),
                'package_number': data.get('package_number', ''),
                'date': date_value,                       # DateField
                'shipping_date': shipping_date,           # DateField
                'delivery_method': data.get('delivery_method', ''),
                'delivery_method_id': data.get('delivery_method_id', ''),
                'tracking_number': data.get('tracking_number', ''),
                'tracking_link': data.get('tracking_link', ''),
                'expected_delivery_date': _parse_dt_any(data.get('expected_delivery_date'), logger),
                'shipment_delivered_date': _parse_dt_any(data.get('shipment_delivered_date'), logger),
                'status': data.get('status', ''),
                'detailed_status': data.get('detailed_status', ''),
                'status_message': data.get('status_message', ''),
                'carrier': data.get('carrier', ''),
                'service': data.get('service', ''),
                'delivery_days': data.get('delivery_days', ''),
                'delivery_guarantee': data.get('delivery_guarantee', False),
                'total_quantity': data.get('total_quantity', 0),
                'customer_id': data.get('customer_id', ''),
                'customer_name': data.get('customer_name', ''),
                'email': data.get('email', ''),
                'phone': data.get('phone', ''),
                'mobile': data.get('mobile', ''),
                'contact_persons': data.get('contact_persons', []),
                'created_by_id': data.get('created_by_id', ''),
                'last_modified_by_id': data.get('last_modified_by_id', ''),
                'created_time': created_time,
                'last_modified_time': last_modified_time,
                'notes': data.get('notes', ''),
                'terms': data.get('terms', ''),
                'is_emailed': data.get('is_emailed', False),
                'is_advanced_tracking_missing': data.get('is_advanced_tracking_missing', False),
                'line_items': data.get('line_items', []),
                'custom_fields': data.get('custom_fields', []),
                'custom_field_hash': data.get('custom_field_hash', {}),
                'shipmentorder_custom_fields': data.get('shipmentorder_custom_fields', []),
                'billing_address': data.get('billing_address', {}),
                'shipping_address': data.get('shipping_address', {}),
                'picklists': data.get('picklists', []),
                'template_id': data.get('template_id', ''),
                'template_name': data.get('template_name', ''),
                'template_type': data.get('template_type', ''),
                'zoho_shipment': zoho_shipment,
            }
        )
        return package
    except IntegrityError:
        _log(logger, 'error', f"Integrity error for package_id={package_id}. Skipping.")
        return None
    except Exception as e:
        _log(logger, 'error', f"Error creating package instance: {e}")
        return None

# =========================================================
# CREATE ITEM ASSETS TRACK INSTANCE
# =========================================================

def create_zoho_item_assets_track_instance(logger, data, date):
    item_id = data.get('itemId', '')
    sku = data.get('sku', '')
    assets = data.get('assets', [])
    try:
        obj = ZohoItemAssetsTrack.objects.create(
            item_id=item_id,
            sku=sku,
            assets=assets,
            created_time=_parse_dt_any(date, logger) or timezone.now(),
        )
        return obj
    except IntegrityError:
        _log(logger, 'error', f"Integrity error for ZohoItemAssetsTrack item_id={item_id}. Skipping.")
        return None
    except Exception as e:
        _log(logger, 'error', f"Error creating ZohoItemAssetsTrack instance: {e}")
        return None
