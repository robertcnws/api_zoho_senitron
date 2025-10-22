from celery import shared_task
from django.utils import timezone
from .services import (
    sync_senitron_inventory_items,
    sync_senitron_inventory_item_assets,
    sync_senitron_inventory_item_assets_logs,
)
from .models import SenitronItemAssetLogs, NotificationUser, Notification

@shared_task
def task_sync_senitron_items():
    return sync_senitron_inventory_items()

@shared_task
def task_load_senitron_inventory_item_assets():
    return sync_senitron_inventory_item_assets()

@shared_task
def task_load_senitron_inventory_item_assets_logs():
    return sync_senitron_inventory_item_assets_logs()

@shared_task
def task_remove_old_senitron_items_assets_logs(days=30):
    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted, _ = SenitronItemAssetLogs.objects.filter(created_time__lt=cutoff).delete()
    return {"deleted": deleted, "cutoff": cutoff.isoformat()}

@shared_task
def task_remove_old_notifications(days=7):
    cutoff = timezone.now() - timezone.timedelta(days=days)
    nu_deleted, _ = NotificationUser.objects.filter(updated_at__lt=cutoff).delete()
    n_deleted, _ = Notification.objects.filter(updated_at__lt=cutoff).delete()
    return {"notification_users_deleted": nu_deleted, "notifications_deleted": n_deleted, "cutoff": cutoff.isoformat()}


# from celery import shared_task
# from django.http import HttpRequest
# from .views import (
#                      load_senitron_inventory_item_assets, 
#                      load_senitron_inventory_item_assets_logs, 
#                      remove_old_senitron_items_assets_logs,
#                      remove_old_notifications
#                 )
# from .services import (
#     sync_senitron_inventory_items,
#     sync_senitron_inventory_item_assets,
#     sync_senitron_inventory_item_assets_logs,
# )
# import json

# @shared_task
# def task_load_senitron_inventory_item_assets():
#     request = HttpRequest()
#     request.method = 'POST'
#     request.content_type = 'application/json'
#     request._body = json.dumps({}).encode('utf-8')
#     load_senitron_inventory_item_assets(request)
    
    
# @shared_task
# def task_load_senitron_inventory_item_assets_logs():
#     request = HttpRequest()
#     request.method = 'POST'
#     request.content_type = 'application/json'
#     request._body = json.dumps({}).encode('utf-8')
#     load_senitron_inventory_item_assets_logs(request)
    
    
# @shared_task
# def task_remove_old_senitron_items_assets_logs():
#     request = HttpRequest()
#     request.method = 'POST'
#     request.content_type = 'application/json'
#     request._body = json.dumps({}).encode('utf-8')
#     remove_old_senitron_items_assets_logs(request)
    
    
# @shared_task
# def task_remove_old_notifications():
#     request = HttpRequest()
#     request.method = 'POST'
#     request.content_type = 'application/json'
#     request._body = json.dumps({}).encode('utf-8')
#     remove_old_notifications(request)