from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
from dateutil.parser import parse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from concurrent.futures import ThreadPoolExecutor, as_completed
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

MAX_WORKERS = 10
BATCH_SIZE = 500
REQUEST_TIMEOUT = 10

def create_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_items(request):
    data = json.loads(request.body) if request.body else {}

    params = {
        'api_key': settings.API_KEY_SENITRON,
        'per_page': 1000,
        'page': 1
    }
    if data.get('item_number'):
        params['item_number'] = data.get('item_number')

    url = settings.API_SENITRON_QUANTITIES_URL
    session = requests.Session()

    items_to_get = []
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        items_to_get = data.get('items', [])
        total_pages = data.get('total_pages', 1)
    except requests.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return JsonResponse({'message': 'Error fetching data from Senitron'}, status=500)
    
    current_page = 1
    while current_page < total_pages:
        current_page += 1
        params['page'] = current_page
        try:
            response = session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            items_to_get.extend(items)
        except requests.RequestException as e:
            logger.error(f"Error fetching page {current_page}: {e}")
            continue

    item_ids = [item['item_number'] for item in items_to_get]
    existing_items = SenitronItem.objects.filter(item_number__in=item_ids)
    existing_items_ids = set(existing_items.values_list('item_number', flat=True))

    new_items = []
    items_to_update = []

    for data_item in items_to_get:
        new_item = create_inventory_item_instance(logger, data_item)
        zoho_item = ZohoInventoryItem.objects.filter(item_id=new_item.item_number).first()
        sku_info = f"SKU: {zoho_item.sku}, " if zoho_item and zoho_item.sku else ''
        if new_item.item_number in existing_items_ids:
            prev_item = existing_items.get(item_number=new_item.item_number)
            items_to_update.append(new_item)
            if int(prev_item.qty) != int(new_item.qty):
                TimelineItem.objects.create(
                    item_number=new_item.item_number,
                    previous_quantity=prev_item.qty,
                    date_previous_quantity=datetime.now(),
                    actual_quantity=new_item.qty,
                    date_actual_quantity=datetime.now(),
                    zoho_item=zoho_item if zoho_item else None,
                    senitron_item=prev_item,
                    text=f"Senitron Item ({sku_info}ID: {new_item.item_number}) quantity changed from {prev_item.qty} to {new_item.qty}"
                )
        else:
            new_items.append(new_item)
            TimelineItem.objects.create(
                item_number=new_item.item_number,
                actual_quantity=new_item.qty,
                date_actual_quantity=datetime.now(),
                zoho_item=zoho_item if zoho_item else None,
                senitron_item=None,
                text=f"Senitron Item ({sku_info}ID: {new_item.item_number}, Qty: {new_item.qty}) created"
            )

    with transaction.atomic():
        if new_items:
            SenitronItem.objects.bulk_create(new_items, batch_size=200, ignore_conflicts=True)
        if items_to_update:
            SenitronItem.objects.bulk_update(
                items_to_update,
                fields=['tags_count', 'qty'],
                batch_size=1000
            )
            
    previous_day = timezone.now()
            
    JobsUpdatingTimes.objects.filter(last_updated__lt=previous_day).delete()
            
    JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    return JsonResponse({'message': 'Senitron Items loaded successfully'}, status=200)



@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_item_assets(request):
    
    data = json.loads(request.body) if request.body else {}
    username = data.get('username', None)
    params = {
        'api_key': settings.API_KEY_SENITRON,
        'per_page': 250  
    }
    if 'item_number' in data:
        params['item_number'] = data['item_number']
    
    with transaction.atomic():
        filter_kwargs = {'read': True}
        if 'item_number' in data:
            filter_kwargs['item_number'] = data['item_number']
        deleted_count, _ = SenitronItemAsset.objects.filter(**filter_kwargs).delete()
        if deleted_count == 0:
            deleted_count, _ = SenitronItemAsset.objects.all().delete()
        logger.info(f"Deleted {deleted_count} SenitronItemAsset records with read=True")
    
    existing_statuses = SenitronStatus.objects.all()
    status_cache = {(status.name, status.senitron_id): status for status in existing_statuses}
    
    item_numbers = set()
    
    for item in data.get('assets', []):
        if 'item_number' in item:
            item_numbers.add(item['item_number'])
    
    existing_items = SenitronItem.objects.filter(item_number__in=item_numbers)
    item_cache = {item.item_number: item for item in existing_items}
    
    url = settings.API_SENITRON_ASSETS_URL
    session = create_session()

    def fetch_and_save_page(page):
        page_params = params.copy()
        page_params['page'] = page
        try:
            response = session.get(url, params=page_params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            items = response.json().get('assets', [])
            items = [item for item in items if item.get('item_number') == page_params['item_number'] in item_numbers] if 'item_number' in page_params else items
            
            assets = []
            for item_data in items:
                asset = create_inventory_item_asset_instance(logger, item_data, status_cache, item_cache)
                if asset:
                    assets.append(asset)
            
            if assets:
                with transaction.atomic():
                    SenitronItemAsset.objects.bulk_create(assets, batch_size=BATCH_SIZE, ignore_conflicts=True)
            
            return len(items) > 0
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return False
    
    page = 1
    has_more = True
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while has_more:
            futures = {executor.submit(fetch_and_save_page, p): p for p in range(page, page + MAX_WORKERS)}
            has_more = False  

            for future in as_completed(futures):
                page_result = future.result()
                if page_result:
                    has_more = True  
            page += MAX_WORKERS
            
    previous_day = timezone.now()
            
    JobsUpdatingTimes.objects.filter(last_updated__lt=previous_day).delete()
            
    JobsUpdatingTimes.objects.create(last_updated=timezone.now())
    
    if username:
        module='senitron_item_assets'
        info='has loaded new info from Senitron Item Assets'
        type='load'
        create_notification(module, info, type, username)
    
    logger.info(f"Senitron Item Assets loaded successfully")
    
    return JsonResponse({'message': 'Senitron Items Assets loaded successfully'}, status=200)



@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_item_assets_logs(request):
    
    data = json.loads(request.body) if request.body else {}
    username = data.get('username', None)
    
    now = timezone.now()
    
    last_time_inserted = SenitronItemAssetLogs.objects.all().order_by('-created_time').first()
    
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    diff = now - last_time_inserted.created_time if last_time_inserted else now - start_of_day
    
    diff_hours = diff.total_seconds() // 3600 
    
    diff_hours = diff_hours if diff_hours > 0 else 1
    
    params = {
        'api_key': settings.API_KEY_SENITRON,
        'per_page': 250,
        'filter_hours': diff_hours 
    }
    if 'item_number' in data:
        params['item_number'] = data['item_number']
    
    item_senitron_ids = set()
    
    for item in data.get('assets', []):
        if 'id' in item:
            item_senitron_ids.add(item['id'])
    
    url = settings.API_SENITRON_ASSETS_LOGS_URL
    session = create_session()

    def fetch_and_save_page(page):
        page_params = params.copy()
        page_params['page'] = page
        try:
            response = session.get(url, params=page_params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            items = response.json().get('assets', [])
            
            items_map = {}

            for item_data in items:
                serial_number = item_data.get('serial_number')
                current_status = item_data.get('current_status', {})
                current_status_id = current_status.get('id')
                current_status_name = current_status.get('name')
                last_status = item_data.get('last_status', {})
                last_status_id = last_status.get('id')
                last_status_name = last_status.get('name')
                last_seen_str = item_data.get('last_seen')
                
                if last_seen_str:
                    last_seen_dt = parse(last_seen_str)
                else:
                    continue

                key = (serial_number, current_status_id, current_status_name, last_status_id, last_status_name)
                
                if key not in items_map or last_seen_dt > items_map[key]['last_seen_dt']:
                # if key not in items_map:
                    items_map[key] = {
                        'item_data': item_data,
                        'last_seen_dt': last_seen_dt
                    }
                    
            selected_items = [v['item_data'] for v in items_map.values() if v['item_data']['current_status']['id'] != v['item_data']['last_status']['id']]
            
            logger.info(f'Selected senitron items assets logs to insert: {len(selected_items)}')
            
            assets = []
            for item_data in selected_items:
                asset = create_inventory_item_asset_logs_instance(logger, item_data)
                if asset:
                    assets.append(asset)
            
            if assets:
                with transaction.atomic():
                    SenitronItemAssetLogs.objects.bulk_create(assets, batch_size=BATCH_SIZE, ignore_conflicts=True)
            
            return len(items) > 0
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return False
    
    page = 1
    has_more = True
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while has_more:
            futures = {executor.submit(fetch_and_save_page, p): p for p in range(page, page + MAX_WORKERS)}
            has_more = False  

            for future in as_completed(futures):
                page_result = future.result()
                if page_result:
                    has_more = True  
            page += MAX_WORKERS
            
    previous_day = timezone.now()
            
    JobsUpdatingTimes.objects.filter(last_updated__lt=previous_day).delete()
            
    JobsUpdatingTimes.objects.create(last_updated=timezone.now())
    
    if username:
        module='senitron_item_assets_logs'
        info='has loaded new info from status logs of Senitron Item Assets'
        type='load'
        create_notification(module, info, type, username)
            
    logger.info(f"Senitron Item Assets Logs loaded successfully")
    
    return JsonResponse({'message': 'Senitron Items Assets Logs loaded successfully'}, status=200)


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
    days_ago = now - timezone.timedelta(days=30)
    NotificationUser.objects.filter(updated_at__lt=days_ago).delete()
    Notification.objects.filter(updated_at__lt=days_ago).delete()
    return JsonResponse({'message': '30 days old Notifications removed successfully'}, status=200)


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


