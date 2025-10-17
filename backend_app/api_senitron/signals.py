from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import (
    SenitronItem, 
    SenitronItemAsset, 
    TimelineItem,
    SenitronItemAssetLogs,
    NotificationUser,
)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from utils.signals_helper import cache_delete_keys, cache_delete_patterns, channels_group_send
import json
import api_senitron.model_serializer as model_serializer

# =========================================================
# SenitronItem  (invalida lista 'all_senitron_inventory_items')
# =========================================================

@receiver(post_save, sender=SenitronItem)
def senitron_inventory_item_saved(sender, instance, created, **kwargs):
    cache_delete_keys(["gql:all_senitron_inventory_items:v1"])
    event = {
        'type': 'send_senitron_item_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._timeline_item_to_message_dict(instance)

        }
    }
    transaction.on_commit(lambda: channels_group_send('senitron_inventory_items', event))
    

@receiver(post_delete, sender=SenitronItem)
def senitron_inventory_item_deleted(sender, instance, **kwargs):
    cache_delete_keys(["gql:all_senitron_inventory_items:v1"])
    event = {
        'type': 'send_senitron_item_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._timeline_item_to_message_dict(instance)

        }
    }
    transaction.on_commit(lambda: channels_group_send('senitron_inventory_items', event))
    
# =========================================================
# SenitronItemAsset  (invalida lista 'all_senitron_inventory_items_assets')
# =========================================================
    
@receiver(post_save, sender=SenitronItemAsset)
def senitron_inventory_item_asset_saved(sender, instance, created, **kwargs):
    cache_delete_keys(["gql:all_senitron_inventory_items_assets:v1"])
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
        asset_data = model_serializer._senitron_item_asset_to_message_dict(asset)
        event['message']['item']['assets'].append(asset_data)
    transaction.on_commit(lambda: channels_group_send('senitron_inventory_items_assets', event))
    

@receiver(post_delete, sender=SenitronItemAsset)
def senitron_inventory_item_asset_deleted(sender, instance, **kwargs):
    cache_delete_keys(["gql:all_senitron_inventory_items_assets:v1"])
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
        asset_data = model_serializer._senitron_item_asset_to_message_dict(asset)
        event['message']['item']['assets'].append(asset_data)
    transaction.on_commit(lambda: channels_group_send('senitron_inventory_items_assets', event))
    
    
# =========================================================
# TimelineItem  (invalida lista 'all_timeline_items')
# =========================================================

@receiver(post_save, sender=TimelineItem)
def senitron_timeline_saved(sender, instance, created, **kwargs):
    cache_delete_keys(["gql:all_timeline_items:v1"])
    event = {
        'type': 'send_senitron_timeline_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._timeline_item_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('senitron_timelines', event))

@receiver(post_delete, sender=TimelineItem)
def senitron_timeline_deleted(sender, instance, **kwargs):
    cache_delete_keys(["gql:all_timeline_items:v1"])
    event = {
        'type': 'send_senitron_timeline_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._timeline_item_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('senitron_timelines', event))
    
# =========================================================
# SenitronItemAssetLogs  (invalida lista 'all_senitron_inventory_items_asset_logs')
# =========================================================
@receiver(post_save, sender=SenitronItemAssetLogs)
def senitron_inventory_item_asset_log_saved(sender, instance, created, **kwargs):
    cache_delete_keys(["gql:all_senitron_grouped_logs:*:v1"])
    event = {
        'type': 'send_senitron_item_asset_log_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._senitron_item_asset_log_to_message_dict(instance)

        }
    }
    transaction.on_commit(lambda: channels_group_send('senitron_inventory_items_asset_logs', event))
    
@receiver(post_delete, sender=SenitronItemAssetLogs)
def senitron_inventory_item_asset_log_deleted(sender, instance, **kwargs):
    cache_delete_keys(["gql:all_senitron_grouped_logs:*:v1"])
    event = {
        'type': 'send_senitron_item_asset_log_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._senitron_item_asset_log_to_message_dict(instance)

        }
    }
    transaction.on_commit(lambda: channels_group_send('senitron_inventory_items_asset_logs', event))
    
# =========================================================
# NotificationUser  (invalida lista 'all_notification_user')
# =========================================================

@receiver(post_save, sender=NotificationUser)
def notification_user_saved(sender, instance, created, **kwargs):
    cache_delete_keys([f"gql:all_notification_user:{instance.user.username}:v1"])
    event = {
        'type': 'send_notification_user_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._notification_user_to_message_dict(instance)

        }
    }
    transaction.on_commit(lambda: channels_group_send('notification_users', event))
    
@receiver(post_delete, sender=NotificationUser)
def notification_user_deleted(sender, instance, **kwargs):
    cache_delete_keys([f"gql:all_notification_user:{instance.user.username}:v1"])
    event = {
        'type': 'send_notification_user_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._notification_user_to_message_dict(instance)

        }
    }
    transaction.on_commit(lambda: channels_group_send('notification_users', event))

