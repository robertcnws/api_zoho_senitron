from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SenitronItem, SenitronItemAsset, TimelineItem
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json


@receiver(post_save, sender=SenitronItem)
def senitron_inventory_item_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_senitron_item_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": {
                "itemNumber": instance.item_number,
                "tagsCount": instance.tags_count,
                "qty": instance.qty,
            }

        }
    }
    async_to_sync(channel_layer.group_send)('senitron_inventory_items', event)
    

@receiver(post_delete, sender=SenitronItem)
def senitron_inventory_item_deleted(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_senitron_item_update',
        'message': {
            'type': 'deleted',
            "item": {
                "itemNumber": instance.item_number,
                "tagsCount": instance.tags_count,
                "qty": instance.qty,
            }
        }
    }
    async_to_sync(channel_layer.group_send)('senitron_inventory_items', event)
    
    
@receiver(post_save, sender=SenitronItemAsset)
def senitron_inventory_item_asset_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    
    event = {
        'type': 'send_senitron_item_asset_update',
        'message': {
            'type': 'created' if created else 'updated',
            'item': {
                'itemNumber': instance.item_number,
                'count': SenitronItemAsset.objects.filter(item_number=instance.item_number).count(),
                'senitronItem': {
                    'itemNumber': instance.senitron_item.item_number if instance.senitron_item else None,
                    'tagsCount': instance.senitron_item.tags_count if instance.senitron_item else None,
                    'qty': instance.senitron_item.qty if instance.senitron_item else None,
                },
                'assets': []
            }
        }
    }
    
    assets = SenitronItemAsset.objects.filter(item_number=instance.item_number).select_related('status')

    for asset in assets:
        asset_data = {
            'id': asset.id,
            'serialNumber': asset.serial_number,
            'altSerial': asset.alt_serial,
            'firstSeen': asset.first_seen.isoformat() if asset.first_seen else None,
            'lastSeen': asset.last_seen.isoformat() if asset.last_seen else None,
            'lastSeenAntenna': asset.last_seen_antenna,
            'lastZone': asset.last_zone,
            'handheldReader': asset.handheld_reader,
            'handheldLastSeen': asset.handheld_last_seen.isoformat() if asset.handheld_last_seen else None,
            'staticZone': asset.static_zone,
            'staticZoneLastUpdate': asset.static_zone_last_update.isoformat() if asset.static_zone_last_update else None,
            'receivingDate': asset.receiving_date.isoformat() if asset.receiving_date else None,
            'currentUnits': asset.current_units,
            'storageUnit': asset.storage_unit,
            'adjustQty': asset.adjust_qty,
            'createdAt': asset.created_at.isoformat() if asset.created_at else None,
            'updatedAt': asset.updated_at.isoformat() if asset.updated_at else None,
            'epc': asset.epc,
            'text3': asset.text3,
            'status': {
                'senitronId': asset.status.senitron_id if asset.status else None,
                'name': asset.status.name if asset.status else None,
            } if asset.status else None
        }
        event['message']['item']['assets'].append(asset_data)
        
    async_to_sync(channel_layer.group_send)('senitron_inventory_items_assets', event)
    

@receiver(post_delete, sender=SenitronItemAsset)
def senitron_inventory_item_asset_deleted(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    
    event = {
        'type': 'send_senitron_item_asset_update',
        'message': {
            'type': 'deleted',
            'item': {
                'itemNumber': instance.item_number,
                'count': SenitronItemAsset.objects.filter(item_number=instance.item_number).count(),
                'senitronItem': {
                    'itemNumber': instance.senitron_item.item_number if instance.senitron_item else None,
                    'tagsCount': instance.senitron_item.tags_count if instance.senitron_item else None,
                    'qty': instance.senitron_item.qty if instance.senitron_item else None,
                },
                'assets': []
            }
        }
    }
    
    assets = SenitronItemAsset.objects.filter(item_number=instance.item_number).select_related('status')

    for asset in assets:
        asset_data = {
            'id': asset.id,
            'serialNumber': asset.serial_number,
            'altSerial': asset.alt_serial,
            'firstSeen': asset.first_seen.isoformat() if asset.first_seen else None,
            'lastSeen': asset.last_seen.isoformat() if asset.last_seen else None,
            'lastSeenAntenna': asset.last_seen_antenna,
            'lastZone': asset.last_zone,
            'handheldReader': asset.handheld_reader,
            'handheldLastSeen': asset.handheld_last_seen.isoformat() if asset.handheld_last_seen else None,
            'staticZone': asset.static_zone,
            'staticZoneLastUpdate': asset.static_zone_last_update.isoformat() if asset.static_zone_last_update else None,
            'receivingDate': asset.receiving_date.isoformat() if asset.receiving_date else None,
            'currentUnits': asset.current_units,
            'storageUnit': asset.storage_unit,
            'adjustQty': asset.adjust_qty,
            'createdAt': asset.created_at.isoformat() if asset.created_at else None,
            'updatedAt': asset.updated_at.isoformat() if asset.updated_at else None,
            'epc': asset.epc,
            'text3': asset.text3,
            'status': {
                'senitronId': asset.status.senitron_id if asset.status else None,
                'name': asset.status.name if asset.status else None,
            } if asset.status else None
        }
        event['message']['item']['assets'].append(asset_data)
        
    async_to_sync(channel_layer.group_send)('senitron_inventory_items_assets', event)
    
    
@receiver(post_save, sender=TimelineItem)
def senitron_timeline_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_senitron_timeline_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": {
                "id": instance.id if instance.id else None,
                "itemNumber": instance.item_number if instance.item_number else None,
                "previousStockOnHand": instance.previous_stock_on_hand if instance.previous_stock_on_hand else None,
                "datePreviousStockOnHand": instance.date_previous_stock_on_hand.isoformat() if instance.date_previous_stock_on_hand else None,
                "actualStockOnHand": instance.actual_stock_on_hand if instance.actual_stock_on_hand else None,
                "dateActualStockOnHand": instance.date_actual_stock_on_hand.isoformat() if instance.date_actual_stock_on_hand else None,
                "previousStatusZoho": instance.previous_status_zoho if instance.previous_status_zoho else None,
                "datePreviousStatusZoho": instance.date_previous_status_zoho.isoformat() if instance.date_previous_status_zoho else None,
                "actualStatusZoho": instance.actual_status_zoho if instance.actual_status_zoho else None,
                "dateActualStatusZoho": instance.date_actual_status_zoho.isoformat() if instance.date_actual_status_zoho else None,
                "previousQuantity": instance.previous_quantity if instance.previous_quantity else None,
                "datePreviousQuantity": instance.date_previous_quantity.isoformat() if instance.date_previous_quantity else None,
                "actualQuantity": instance.actual_quantity if instance.actual_quantity else None,
                "dateActualQuantity": instance.date_actual_quantity.isoformat() if instance.date_actual_quantity else None,
                "previousStatusSenitron": {
                    "id": instance.previous_status_senitron.id if instance.previous_status_senitron else None,
                    "senitronId": instance.previous_status_senitron.senitron_id if instance.previous_status_senitron else None,
                    "name": instance.previous_status_senitron.name if instance.previous_status_senitron else None,
                },
                "datePreviousStatusSenitron": instance.date_previous_status_senitron.isoformat() if instance.date_previous_status_senitron else None,
                "actualStatusSenitron": {
                    "id": instance.actual_status_senitron.id if instance.actual_status_senitron else None,
                    "senitronId": instance.actual_status_senitron.senitron_id if instance.actual_status_senitron else None,
                    "name": instance.actual_status_senitron.name if instance.actual_status_senitron else None,
                },
                "dateActualStatusSenitron": instance.date_actual_status_senitron.isoformat() if instance.date_actual_status_senitron else None,
                "senitronItem": {
                    "itemNumber": instance.senitron_item.item_number if instance.senitron_item else None,
                    "qty": instance.senitron_item.qty if instance.senitron_item else None,
                    "tagsCount": instance.senitron_item.tags_count if instance.senitron_item else None,
                },
                "zohoItem": {
                    "itemId": instance.zoho_item.item_id if instance.zoho_item else None,
                    "name": instance.zoho_item.name if instance.zoho_item else None,
                    "sku": instance.zoho_item.sku if instance.zoho_item else None,
                    "stockOnHand": instance.zoho_item.stock_on_hand if instance.zoho_item else None,
                },
                "text": instance.text,
            }
        }
    }
    async_to_sync(channel_layer.group_send)('senitron_timeline', event)

@receiver(post_delete, sender=TimelineItem)
def senitron_timeline_deleted(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    event = {
        'type': 'send_senitron_timeline_update',
        'message': {
            'type': 'deleted',
            "item": {
                "id": instance.id if instance.id else None,
                "itemNumber": instance.item_number if instance.item_number else None,
                "previousStockOnHand": instance.previous_stock_on_hand if instance.previous_stock_on_hand else None,
                "datePreviousStockOnHand": instance.date_previous_stock_on_hand.isoformat() if instance.date_previous_stock_on_hand else None,
                "actualStockOnHand": instance.actual_stock_on_hand if instance.actual_stock_on_hand else None,
                "dateActualStockOnHand": instance.date_actual_stock_on_hand.isoformat() if instance.date_actual_stock_on_hand else None,
                "previousStatusZoho": instance.previous_status_zoho if instance.previous_status_zoho else None,
                "datePreviousStatusZoho": instance.date_previous_status_zoho.isoformat() if instance.date_previous_status_zoho else None,
                "actualStatusZoho": instance.actual_status_zoho if instance.actual_status_zoho else None,
                "dateActualStatusZoho": instance.date_actual_status_zoho.isoformat() if instance.date_actual_status_zoho else None,
                "previousQuantity": instance.previous_quantity if instance.previous_quantity else None,
                "datePreviousQuantity": instance.date_previous_quantity.isoformat() if instance.date_previous_quantity else None,
                "actualQuantity": instance.actual_quantity if instance.actual_quantity else None,
                "dateActualQuantity": instance.date_actual_quantity.isoformat() if instance.date_actual_quantity else None,
                "previousStatusSenitron": {
                    "id": instance.previous_status_senitron.id if instance.previous_status_senitron else None,
                    "senitronId": instance.previous_status_senitron.senitron_id if instance.previous_status_senitron else None,
                    "name": instance.previous_status_senitron.name if instance.previous_status_senitron else None,
                },
                "datePreviousStatusSenitron": instance.date_previous_status_senitron.isoformat() if instance.date_previous_status_senitron else None,
                "actualStatusSenitron": {
                    "id": instance.actual_status_senitron.id if instance.actual_status_senitron else None,
                    "senitronId": instance.actual_status_senitron.senitron_id if instance.actual_status_senitron else None,
                    "name": instance.actual_status_senitron.name if instance.actual_status_senitron else None,
                },
                "dateActualStatusSenitron": instance.date_actual_status_senitron.isoformat() if instance.date_actual_status_senitron else None,
                "senitronItem": {
                    "itemNumber": instance.senitron_item.item_number if instance.senitron_item else None,
                    "qty": instance.senitron_item.qty if instance.senitron_item else None,
                    "tagsCount": instance.senitron_item.tags_count if instance.senitron_item else None,
                },
                "zohoItem": {
                    "itemId": instance.zoho_item.item_id if instance.zoho_item else None,
                    "name": instance.zoho_item.name if instance.zoho_item else None,
                    "sku": instance.zoho_item.sku if instance.zoho_item else None,
                    "stockOnHand": instance.zoho_item.stock_on_hand if instance.zoho_item else None,
                },
                "text": instance.text,
            }
        }
    }
    async_to_sync(channel_layer.group_send)('senitron_timeline', event)
