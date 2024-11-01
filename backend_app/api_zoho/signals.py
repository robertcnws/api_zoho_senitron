from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ZohoInventoryItem, ZohoInventoryShipmentSalesOrder
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

@receiver(post_save, sender=ZohoInventoryItem)
def inventory_item_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_item_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": {
                "groupId": instance.group_id,
                "groupName": instance.group_name,
                "itemId": instance.item_id,
                "name": instance.name,
                "status": instance.status,
                "source": instance.source,
                "itemType": instance.item_type,
                "isLinkedWithZohocrm": instance.is_linked_with_zohocrm,
                "description": instance.description,
                "rate": float(instance.rate) if instance.rate is not None else None,
                "isTaxable": instance.is_taxable,
                "taxId": instance.tax_id,
                "taxName": instance.tax_name,
                "taxPercentage": float(instance.tax_percentage) if instance.tax_percentage is not None else None,
                "purchaseDescription": instance.purchase_description,
                "purchaseRate": float(instance.purchase_rate) if instance.purchase_rate is not None else None,
                "isComboProduct": instance.is_combo_product,
                "syncedWithSenitron": instance.synced_with_senitron,
                "productType": instance.product_type,
                "attributeId1": instance.attribute_id1,
                "attributeName1": instance.attribute_name1,
                "reorderLevel": float(instance.reorder_level) if instance.reorder_level is not None else None,
                "stockOnHand": float(instance.stock_on_hand) if instance.stock_on_hand is not None else None,
                "availableStock": float(instance.available_stock) if instance.available_stock is not None else None,
                "actualAvailableStock": float(instance.actual_available_stock) if instance.actual_available_stock is not None else None,
                "sku": instance.sku,
                "upc": instance.upc,
                "ean": instance.ean,
                "isbn": instance.isbn,
                "partNumber": instance.part_number,
                "attributeOptionId1": instance.attribute_option_id1,
                "attributeOptionName1": instance.attribute_option_name1,
                "createdTime": instance.created_time.isoformat() if instance.created_time else None,
                "lastModifiedTime": instance.last_modified_time.isoformat() if instance.last_modified_time else None,
                "hsnOrSac": instance.hsn_or_sac,
                "satItemKeyCode": instance.sat_item_key_code,
                "unitkeyCode": instance.unitkey_code
            }

        }
    }
    async_to_sync(channel_layer.group_send)('inventory_items', event)

@receiver(post_delete, sender=ZohoInventoryItem)
def inventory_item_deleted(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_item_update',
        'message': {
            'type': 'deleted',
            "item": {
                "groupId": instance.group_id,
                "groupName": instance.group_name,
                "itemId": instance.item_id,
                "name": instance.name,
                "status": instance.status,
                "source": instance.source,
                "itemType": instance.item_type,
                "isLinkedWithZohocrm": instance.is_linked_with_zohocrm,
                "description": instance.description,
                "rate": float(instance.rate) if instance.rate is not None else None,
                "isTaxable": instance.is_taxable,
                "taxId": instance.tax_id,
                "taxName": instance.tax_name,
                "taxPercentage": float(instance.tax_percentage) if instance.tax_percentage is not None else None,
                "purchaseDescription": instance.purchase_description,
                "purchaseRate": float(instance.purchase_rate) if instance.purchase_rate is not None else None,
                "isComboProduct": instance.is_combo_product,
                "syncedWithSenitron": instance.synced_with_senitron,
                "productType": instance.product_type,
                "attributeId1": instance.attribute_id1,
                "attributeName1": instance.attribute_name1,
                "reorderLevel": float(instance.reorder_level) if instance.reorder_level is not None else None,
                "stockOnHand": float(instance.stock_on_hand) if instance.stock_on_hand is not None else None,
                "availableStock": float(instance.available_stock) if instance.available_stock is not None else None,
                "actualAvailableStock": float(instance.actual_available_stock) if instance.actual_available_stock is not None else None,
                "sku": instance.sku,
                "upc": instance.upc,
                "ean": instance.ean,
                "isbn": instance.isbn,
                "partNumber": instance.part_number,
                "attributeOptionId1": instance.attribute_option_id1,
                "attributeOptionName1": instance.attribute_option_name1,
                "createdTime": instance.created_time.isoformat() if instance.created_time else None,
                "lastModifiedTime": instance.last_modified_time.isoformat() if instance.last_modified_time else None,
                "hsnOrSac": instance.hsn_or_sac,
                "satItemKeyCode": instance.sat_item_key_code,
                "unitkeyCode": instance.unitkey_code
            }
        }
    }
    async_to_sync(channel_layer.group_send)('inventory_items', event)
    
    
@receiver(post_save, sender=ZohoInventoryShipmentSalesOrder)
def inventory_sales_order_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_sales_order_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": {
                "salesorderId": instance.salesorder_id,
                "salesorderNumber": instance.salesorder_number,
                "date": instance.date.isoformat() if instance.date else None,
                "status": instance.status,
                "lineItems": instance.line_items,
                "customerId": instance.customer_id,
                "customerName": instance.customer_name,
                "isTaxable": instance.is_taxable,
                "taxId": instance.tax_id,
                "taxName": instance.tax_name,
                "taxPercentage": instance.tax_percentage,
                "currencyId": instance.currency_id,
                "currencyCode": instance.currency_code,
                "currencySymbol": instance.currency_symbol,
                "exchangeRate": instance.exchange_rate,
                "deliveryMethod": instance.delivery_method,
                "totalQuantity": instance.total_quantity,
                "subTotal": instance.sub_total,
                "taxTotal": instance.tax_total,
                "total": instance.total,
                "createdByEmail": instance.created_by_email,
                "createdByName": instance.created_by_name,
                "salespersonId": instance.salesperson_id,
                "isTestOrder": instance.is_test_order,
                "notes": instance.notes,
                "paymentTerms": instance.payment_terms,
                "paymentTermsLabel": instance.payment_terms_label,
                "shippingAddress": instance.shipping_address,
                "billingAddress": instance.billing_address,
                "warehouses": instance.warehouses,
                "customFields": instance.custom_fields,
                "orderSubStatuses": instance.order_sub_statuses,
                "shipmentSubStatuses": instance.shipment_sub_statuses,
                "createdTime": instance.created_time.isoformat() if instance.created_time else None,
                "lastModifiedTime": instance.last_modified_time.isoformat() if instance.last_modified_time else None,
            }
        }
    }
    async_to_sync(channel_layer.group_send)('inventory_sales_order', event)

@receiver(post_delete, sender=ZohoInventoryShipmentSalesOrder)
def inventory_sales_order_deleted(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_sales_order_update',
        'message': {
            'type': 'deleted',
            "item": {
                "salesorderId": instance.salesorder_id,
                "salesorderNumber": instance.salesorder_number,
                "date": instance.date.isoformat() if instance.date else None,
                "status": instance.status,
                "lineItems": instance.line_items,
                "customerId": instance.customer_id,
                "customerName": instance.customer_name,
                "isTaxable": instance.is_taxable,
                "taxId": instance.tax_id,
                "taxName": instance.tax_name,
                "taxPercentage": instance.tax_percentage,
                "currencyId": instance.currency_id,
                "currencyCode": instance.currency_code,
                "currencySymbol": instance.currency_symbol,
                "exchangeRate": instance.exchange_rate,
                "deliveryMethod": instance.delivery_method,
                "totalQuantity": instance.total_quantity,
                "subTotal": instance.sub_total,
                "taxTotal": instance.tax_total,
                "total": instance.total,
                "createdByEmail": instance.created_by_email,
                "createdByName": instance.created_by_name,
                "salespersonId": instance.salesperson_id,
                "isTestOrder": instance.is_test_order,
                "notes": instance.notes,
                "paymentTerms": instance.payment_terms,
                "paymentTermsLabel": instance.payment_terms_label,
                "shippingAddress": instance.shipping_address,
                "billingAddress": instance.billing_address,
                "warehouses": instance.warehouses,
                "customFields": instance.custom_fields,
                "orderSubStatuses": instance.order_sub_statuses,
                "shipmentSubStatuses": instance.shipment_sub_statuses,
                "createdTime": instance.created_time.isoformat() if instance.created_time else None,
                "lastModifiedTime": instance.last_modified_time.isoformat() if instance.last_modified_time else None,
            }
        }
    }
    async_to_sync(channel_layer.group_send)('inventory_sales_order', event)
