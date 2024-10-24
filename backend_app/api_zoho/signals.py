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
                "itemId": instance.item_id,
                "name": instance.name,
                "sku": instance.sku,
                "status": instance.status,
                "stockOnHand": instance.stock_on_hand,
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
                "itemId": instance.item_id,
                "name": instance.name,
                "sku": instance.sku,
                "status": instance.status,
                "stockOnHand": instance.stock_on_hand,
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
