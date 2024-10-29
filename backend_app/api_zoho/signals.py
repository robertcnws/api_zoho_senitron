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
                "rate": instance.rate,
                "isTaxable": instance.is_taxable,
                "taxId": instance.tax_id,
                "taxName": instance.tax_name,
                "taxPercentage": instance.tax_percentage,
                "purchaseDescription": instance.purchase_description,
                "purchaseRate": instance.purchase_rate,
                "isComboProduct": instance.is_combo_product,
                "syncedWithSenitron": instance.synced_with_senitron,
                "productType": instance.product_type,
                "attributeId1": instance.attribute_id1,
                "attributeName1": instance.attribute_name1,
                "reorderLevel": instance.reorder_level,
                "stockOnHand": instance.stock_on_hand,
                "availableStock": instance.available_stock,
                "actualAvailableStock": instance.actual_available_stock,
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
                "rate": instance.rate,
                "isTaxable": instance.is_taxable,
                "taxId": instance.tax_id,
                "taxName": instance.tax_name,
                "taxPercentage": instance.tax_percentage,
                "purchaseDescription": instance.purchase_description,
                "purchaseRate": instance.purchase_rate,
                "isComboProduct": instance.is_combo_product,
                "syncedWithSenitron": instance.synced_with_senitron,
                "productType": instance.product_type,
                "attributeId1": instance.attribute_id1,
                "attributeName1": instance.attribute_name1,
                "reorderLevel": instance.reorder_level,
                "stockOnHand": instance.stock_on_hand,
                "availableStock": instance.available_stock,
                "actualAvailableStock": instance.actual_available_stock,
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
            }
        }
    }
    async_to_sync(channel_layer.group_send)('inventory_sales_order', event)
