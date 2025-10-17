from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import (
    ZohoInventoryItem,
    ZohoInventoryShipmentSalesOrder,
    ZohoShipmentOrder,
    ZohoPackage,
    ZohoItemAssetsTrack,
    ZohoSkuTrackInfo,
    LoginUser,
    JobsUpdatingTimes,
    ManualUpdatingJobs,
)
from django.db import transaction
from utils.signals_helper import cache_delete_keys, cache_delete_patterns, channels_group_send
import api_zoho.model_serializer as model_serializer

# =========================================================
# ZohoInventoryItem  (invalida lista 'all_zoho_inventory_items')
# =========================================================
@receiver(post_save, sender=ZohoInventoryItem)
def inventory_item_saved(sender, instance, created, **kwargs):
    cache_delete_keys(["gql:all_zoho_inventory_items:v1"])

    event = {
        'type': 'send_item_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._inventory_item_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_items', event))

@receiver(post_delete, sender=ZohoInventoryItem)
def inventory_item_deleted(sender, instance, **kwargs):
    cache_delete_keys(["gql:all_zoho_inventory_items:v1"])

    event = {
        'type': 'send_item_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._inventory_item_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_items', event))


# =========================================================
# ZohoInventoryShipmentSalesOrder  (lista con filtros por fecha)
# Cache key en resolver: f"gql:all_zoho_inventory_sales_orders:{start}:{end}:v1"
# =========================================================
@receiver(post_save, sender=ZohoInventoryShipmentSalesOrder)
def inv_sales_order_saved(sender, instance, created, **kwargs):
    cache_delete_patterns(["gql:all_zoho_inventory_sales_orders:*:*:v1"])
    event = {
        'type': 'send_sales_order_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._sales_order_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_sales_order', event))

@receiver(post_delete, sender=ZohoInventoryShipmentSalesOrder)
def inv_sales_order_deleted(sender, instance, **kwargs):
    cache_delete_patterns(["gql:all_zoho_inventory_sales_orders:*:*:v1"])
    event = {
        'type': 'send_sales_order_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._sales_order_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_sales_order', event))


# =========================================================
# ZohoShipmentOrder  (cache key: f"gql:all_zoho_shipment_orders:{start}:{end}:v1")
# =========================================================
    
@receiver(post_save, sender=ZohoShipmentOrder)
def shipment_order_saved(sender, instance, created, **kwargs):
    cache_delete_patterns(["gql:all_zoho_shipment_orders:*:*:v1"])
    event = {
        'type': 'send_shipment_order_update',
        'message': {
            'type': 'created' if created else 'updated',
            'item': model_serializer._shipment_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_shipment_order', event))

@receiver(post_delete, sender=ZohoShipmentOrder)
def shipment_order_deleted(sender, instance, **kwargs):
    cache_delete_patterns(["gql:all_zoho_shipment_orders:*:*:v1"])
    event = {
        'type': 'send_shipment_order_update',
        'message': {
            'type': 'deleted',
            'item': model_serializer._shipment_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_shipment_order', event))


# =========================================================
# ZohoPackage  (cache key: "gql:all_zoho_packages:v1" solo para “sin filtros”)
# =========================================================
@receiver(post_save, sender=ZohoPackage)
def package_saved(sender, instance, created, **kwargs):
    cache_delete_keys(["gql:all_zoho_packages:v1"])
    event = {
        'type': 'send_package_update',
        'message': {
            'type': 'created' if created else 'updated',
            'item': model_serializer._package_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_packages', event))

@receiver(post_delete, sender=ZohoPackage)
def package_deleted(sender, instance, **kwargs):
    cache_delete_keys(["gql:all_zoho_packages:v1"])
    event = {
        'type': 'send_package_update',
        'message': {
            'type': 'deleted',
            'item': model_serializer._package_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_packages', event))


# =========================================================
# ZohoSkuTrackInfo  (cache key: "gql:all_zoho_sku_track_info:v1")
# =========================================================
@receiver(post_save, sender=ZohoSkuTrackInfo)
def sku_track_saved(sender, instance, created, **kwargs):
    cache_delete_keys(["gql:all_zoho_sku_track_info:v1"])
    event = {
        'type': 'send_sku_track_update',
        'message': {
            'type': 'created' if created else 'updated',
            'item': model_serializer._sku_track_info_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_sku_track_info', event))

@receiver(post_delete, sender=ZohoSkuTrackInfo)
def sku_track_deleted(sender, instance, **kwargs):
    cache_delete_keys(["gql:all_zoho_sku_track_info:v1"])
    event = {
        'type': 'send_sku_track_update',
        'message': {
            'type': 'deleted',
            'item': model_serializer._sku_track_info_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_sku_track_info', event))


# =========================================================
# ZohoItemAssetsTrack  (cache key: f"gql:all_zoho_item_assets_track:{item_id}:{list_ids}:v1")
# Como hay muchas combinaciones, borramos por patrón y una específica por item_id
# =========================================================
@receiver(post_save, sender=ZohoItemAssetsTrack)
def item_assets_track_saved(sender, instance, created, **kwargs):
    cache_delete_patterns(["gql:all_zoho_item_assets_track:*:v1"])
    cache_delete_patterns([f"gql:all_zoho_item_assets_track:{instance.item_id}:*:v1"])
    event = {
        'type': 'send_item_assets_track_update',
        'message': {
            'type': 'created' if created else 'updated',
            'item': model_serializer._item_assets_track_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_item_assets_track', event))

@receiver(post_delete, sender=ZohoItemAssetsTrack)
def item_assets_track_deleted(sender, instance, **kwargs):
    cache_delete_patterns(["gql:all_zoho_item_assets_track:*:v1"])
    cache_delete_patterns([f"gql:all_zoho_item_assets_track:{instance.item_id}:*:v1"])
    event = {
        'type': 'send_item_assets_track_update',
        'message': {
            'type': 'deleted',
            'item': model_serializer._item_assets_track_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('inventory_item_assets_track', event))


# =========================================================
# LoginUser (no cacheado en tu schema actual; solo eventos)
# =========================================================
@receiver(post_save, sender=LoginUser)
def login_user_saved(sender, instance, created, **kwargs):
    event = {
        'type': 'send_login_user_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._login_user_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('login_users', event))

@receiver(post_delete, sender=LoginUser)
def login_user_deleted(sender, instance, **kwargs):
    event = {
        'type': 'send_login_user_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._login_user_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('login_users', event))
    
# =========================================================
# JobsUpdatingTimes (no cacheado en tu schema actual; solo eventos)
# =========================================================

@receiver(post_save, sender=JobsUpdatingTimes)
def jobs_updating_times_saved(sender, instance, created, **kwargs):
    event = {
        'type': 'send_jobs_updating_times_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._jobs_updating_times_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('jobs_updating_times', event))
    
@receiver(post_delete, sender=JobsUpdatingTimes)
def jobs_updating_times_deleted(sender, instance, **kwargs):
    event = {
        'type': 'send_jobs_updating_times_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._jobs_updating_times_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('jobs_updating_times', event))
    
# =========================================================
# ManualUpdatingJobs (no cacheado en tu schema actual; solo eventos)
# =========================================================
@receiver(post_save, sender=ManualUpdatingJobs)
def manual_updating_jobs_saved(sender, instance, created, **kwargs):
    event = {
        'type': 'send_manual_updating_jobs_update',
        'message': {
            'type': 'created' if created else 'updated',
            "item": model_serializer._manual_updating_jobs_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('manual_updating_jobs', event))
    
@receiver(post_delete, sender=ManualUpdatingJobs)
def manual_updating_jobs_deleted(sender, instance, **kwargs):
    event = {
        'type': 'send_manual_updating_jobs_update',
        'message': {
            'type': 'deleted',
            "item": model_serializer._manual_updating_jobs_to_message_dict(instance)
        }
    }
    transaction.on_commit(lambda: channels_group_send('manual_updating_jobs', event))