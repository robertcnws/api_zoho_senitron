from datetime import datetime as dt
from django.utils import timezone
from .models import ZohoInventoryItem, ZohoInventoryShipmentSalesOrder
from django.db.utils import IntegrityError

#############################################
# CREATE ITEM INVENTORY INSTANCE
#############################################

def create_inventory_item_instance(logger, data):
    
    current_timezone = timezone.get_current_timezone()
    
    created_time_str = data.get('created_time', None)
    created_time = dt.strptime(created_time_str, '%Y-%m-%dT%H:%M:%S%z') if created_time_str else None
    
    if created_time and created_time.tzinfo is None:
        created_time = current_timezone.localize(created_time)
    
    last_modified_time_str = data.get('last_modified_time', None)
    last_modified_time = dt.strptime(last_modified_time_str, '%Y-%m-%dT%H:%M:%S%z') if last_modified_time_str else None
    
    if last_modified_time and last_modified_time.tzinfo is None:
        last_modified_time = current_timezone.localize(last_modified_time)
    
    item_id=data.get('item_id', '')
    
    try:
        obj, _ = ZohoInventoryItem.objects.update_or_create(
            item_id=item_id,
            defaults={
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
                'unitkey_code': data.get('unitkey_code', '')
            }
        )
        return obj
    except IntegrityError:
        logger.error(f"Integrity error for item_id={item_id}. Skipping.")
        return None


#############################################
# CREATE SALES ORDER INVENTORY INSTANCE
#############################################

def create_inventory_sales_order_instance(logger, data):
    
    current_timezone = timezone.get_current_timezone()
    
    date_str = data.get('date', None)
    date = dt.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    
    created_time_str = data.get('created_time', None)
    created_time = dt.strptime(created_time_str, '%Y-%m-%dT%H:%M:%S%z') if created_time_str else None
    
    if created_time and created_time.tzinfo is None:
        created_time = current_timezone.localize(created_time)
    
    last_modified_time_str = data.get('last_modified_time', None)
    last_modified_time = dt.strptime(last_modified_time_str, '%Y-%m-%dT%H:%M:%S%z') if last_modified_time_str else None
    
    if last_modified_time and last_modified_time.tzinfo is None:
        last_modified_time = current_timezone.localize(last_modified_time)
    
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
                'date': date,
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
        logger.error(f"Integrity error for salesorder_id={salesorder_id}. Skipping.")
        return None
    
    
    
    