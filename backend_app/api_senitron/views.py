from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
from dateutil.parser import parse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from concurrent.futures import ThreadPoolExecutor, as_completed
from .services import (
    _create_session as create_session,
    sync_senitron_inventory_items,
    sync_senitron_inventory_item_assets,
    sync_senitron_inventory_item_assets_logs,
)
from .models import (
                    SenitronItem, 
                    SenitronItemAsset, 
                    TimelineItem, 
                    SenitronStatus, 
                    SenitronItemAssetLogs,
                    Notification,
                    NotificationUser
                )
from api_zoho.models import (
                    ZohoInventoryItem, 
                    JobsUpdatingTimes,
                    LoginUser
                )
from .manage_instances import (
                              create_inventory_item_instance, 
                              create_inventory_item_asset_instance, 
                              create_inventory_item_asset_logs_instance
                            )
from datetime import datetime
from django.utils import timezone
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import requests
import logging
import json


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_items(request):
    data = json.loads(request.body) if request.body else {}
    item_number = data.get('item_number')
    out = sync_senitron_inventory_items(item_number=item_number)
    return JsonResponse({'message': 'Senitron Items loaded successfully', 'stats': out}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_item_assets(request):
    data = json.loads(request.body) if request.body else {}
    username = data.get('username')
    item_number = data.get('item_number')
    assets_hint = data.get('assets')
    out = sync_senitron_inventory_item_assets(item_number=item_number, assets_hint=assets_hint)
    if username:
        create_notification('senitron_item_assets', 'has loaded new info from Senitron Item Assets', 'load', username)
    return JsonResponse({'message': 'Senitron Items Assets loaded successfully', 'stats': out}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_item_assets_logs(request):
    data = json.loads(request.body) if request.body else {}
    username = data.get('username')
    item_number = data.get('item_number')
    out = sync_senitron_inventory_item_assets_logs(item_number=item_number)
    if username:
        create_notification('senitron_item_assets_logs', 'has loaded new info from status logs of Senitron Item Assets', 'load', username)
    return JsonResponse({'message': 'Senitron Items Assets Logs loaded successfully', 'stats': out}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def remove_old_senitron_items_assets_logs(request):
    now = timezone.now()
    days_ago = now - timezone.timedelta(days=30)
    SenitronItemAssetLogs.objects.filter(created_time__lt=days_ago).delete()
    return JsonResponse({'message': '30 days old Senitron Items Assets Logs removed successfully'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def notifications_mark_all_as_read(request):
    now = timezone.now()
    data = json.loads(request.body) if request.body else {}
    username = data.get('username', None)
    if username:
        user = LoginUser.objects.filter(username=username).first()
        if user:
            NotificationUser.objects.filter(user=user).update(read=True, updated_at=now)
            return JsonResponse({'message': 'All notifications marked as read'}, status=200)
        return JsonResponse({'message': 'User not found'}, status=404)
    return JsonResponse({'message': 'Username not provided'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def notification_mark_as_read(request, notification_id):
    now = timezone.now()
    notification_user = NotificationUser.objects.filter(id=notification_id).first()
    if notification_user:
        notification_user.read = True
        notification_user.updated_at = now
        notification_user.save()
        return JsonResponse({'message': 'Notification marked as read'}, status=200)
    return JsonResponse({'message': 'Notification not found'}, status=404)
    


@api_view(['POST'])
@permission_classes([AllowAny])
def remove_old_notifications(request):
    now = timezone.now()
    days_ago = now - timezone.timedelta(days=7)
    NotificationUser.objects.filter(updated_at__lt=days_ago).delete()
    Notification.objects.filter(updated_at__lt=days_ago).delete()
    return JsonResponse({'message': '7 days old Notifications removed successfully'}, status=200)


# EXTRA FUNCTIONS

def create_notification(module, info, type, username):
    notification = Notification.objects.create(
        module=module,
        info=info,
        type=type,
    )
    
    user = LoginUser.objects.filter(username=username).first()
    
    username = user.username if user else 'System Job'
    
    all_users = LoginUser.objects.all()
    
    for user in all_users:
        NotificationUser.objects.create(
            notification=notification,
            username=username,
            user=user
        )
    
    return notification


