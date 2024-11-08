from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import SenitronItem, SenitronItemAsset, TimelineItem
from api_zoho.models import ZohoInventoryItem
from .manage_instances import create_inventory_item_instance, create_inventory_item_asset_instance
from datetime import datetime

import requests
import logging
import json


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MAX_WORKERS = 5

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

    return JsonResponse({'message': 'Senitron Items loaded successfully'}, status=200)



@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_item_assets(request):
    
    data = json.loads(request.body) if request.body else {}
    
    params = {
        'api_key': settings.API_KEY_SENITRON,
        'per_page': 500
    }
    if data.get('item_number'):
        params['item_number'] = data.get('item_number')
    
    with transaction.atomic():
        deleted_count, _ = SenitronItemAsset.objects.filter(read=True, item_number=params['item_number']).delete() \
                          if data.get('item_number') else SenitronItemAsset.objects.filter(read=True).delete() 
        logger.info(f"Deleted {deleted_count} SenitronItemAsset records with read=True")

    url = settings.API_SENITRON_ASSETS_URL
    session = requests.Session()

    def fetch_page(page):
        try:
            page_params = params.copy()
            page_params['page'] = page
            response = session.get(url, params=page_params)
            response.raise_for_status()
            data = response.json()
            return data.get('assets', [])
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return []

    items_to_get = []
    page = 1
    while True:
        pages = list(range(page, page + MAX_WORKERS))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_page, p): p for p in pages}
            all_empty = True
            for future in as_completed(futures):
                page_items = future.result()
                if page_items:
                    all_empty = False
                    items_to_get.extend(page_items)
            if all_empty:
                break
            page += MAX_WORKERS

    new_items = []
    
    if data.get('item_number'):
        items_to_get = [item for item in items_to_get if item.get('item_number') == data.get('item_number')]
        
    for item in items_to_get:
        try:
            new_item = create_inventory_item_asset_instance(logger, item)
            new_items.append(new_item)
        except Exception as e:
            logger.error(f"Error processing item {item.get('id')}: {e}")

    with transaction.atomic():
        if new_items:
            SenitronItemAsset.objects.bulk_create(new_items, batch_size=500, ignore_conflicts=True)

    return JsonResponse({'message': 'Senitron Items Assets loaded successfully'}, status=200)
