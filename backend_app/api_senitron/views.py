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

MAX_WORKERS = 20

@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_items(request):
    
    data = json.loads(request.body) if request.body else {}
    
    params = {
        'api_key': settings.API_KEY_SENITRON,
        'per_page': 200,
        'page': 1
    }
    if data.get('item_number'):
        params['item_number'] = data.get('item_number')
        
    url = settings.API_SENITRON_QUANTITIES_URL
    items_to_get = []
    session = requests.Session()
    
    def fetch_page_data(page):
        try:
            params['page'] = page
            response = session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', []), data.get('total_pages', 1)
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return [], 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        initial_items, total_pages = fetch_page_data(1)
        items_to_get.extend(initial_items)
        futures = {executor.submit(fetch_page_data, page): page for page in range(2, total_pages + 1)}
        for future in as_completed(futures):
            page_items, _ = future.result()
            items_to_get.extend(page_items)

    item_ids = [item['item_number'] for item in items_to_get]
    existing_items = SenitronItem.objects.filter(item_number__in=item_ids)
    existing_items_ids = set(existing_items.values_list('item_number', flat=True))

    new_items = []
    items_to_update = []

    for data in items_to_get:
        new_item = create_inventory_item_instance(logger, data)
        zoho_item = ZohoInventoryItem.objects.filter(item_id=new_item.item_number).first()
        sku_info = f"SKU: {zoho_item.sku}, " if zoho_item and zoho_item.sku else ''
        if new_item.item_number in existing_items_ids:
            prev_item = existing_items.get(item_number=new_item.item_number)
            items_to_update.append(new_item)
            print('Prev Item', prev_item.qty)
            print('New Item', new_item.qty)
            print('---------------------------------')
            if int(prev_item.qty) != int(new_item.qty):
                TimelineItem.objects.create(
                    item_number=new_item.item_number, 
                    previous_quantity=prev_item.qty,
                    date_previous_quantity=datetime.now(),
                    actual_quantity=new_item.qty,
                    date_actual_quantity=datetime.now(),
                    zoho_item=zoho_item if zoho_item else None,
                    senitron_item=SenitronItem.objects.filter(item_number=new_item.item_number).first(),
                    text=f"Senitron Item ({sku_info}ID: {new_item.item_number}) quantity changed from {prev_item.qty} to {new_item.qty}"
                ).save()
        else:
            new_items.append(new_item)
            TimelineItem.objects.create(
                item_number=new_item.item_number, 
                actual_quantity=new_item.qty,
                date_actual_quantity=datetime.now(),
                zoho_item=zoho_item if zoho_item else None,
                senitron_item=SenitronItem.objects.filter(item_number=new_item.item_number).first(),
                text=f"Senitron Item ({sku_info}ID: {new_item.item_number}, Qty: {new_item.qty}) created"
            ).save()
    
    with transaction.atomic():
        if new_items:
            SenitronItem.objects.bulk_create(new_items, batch_size=200, ignore_conflicts=True)
        if items_to_update:
            SenitronItem.objects.bulk_update(
                items_to_update,
                fields=[
                    'tags_count',
                    'qty'
                ],
                batch_size=200
            )

    return JsonResponse({'message': 'Senitron Items loaded successfully'}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def load_senitron_inventory_item_assets(request):
    
    data = json.loads(request.body) if request.body else {}
    
    params = {
        'api_key': settings.API_KEY_SENITRON,
        'per_page': 200,
        'page': 1
    }
    if data.get('item_number'):
        params['item_number'] = data.get('item_number')
        
    url = settings.API_SENITRON_ASSETS_URL
    items_to_get = []
    session = requests.Session()
    
    def fetch_page_data(page):
        try:
            params['page'] = page
            response = session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('assets', []), data.get('total_pages', 1)
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return [], 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        initial_items, total_pages = fetch_page_data(1)
        items_to_get.extend(initial_items)
        futures = {executor.submit(fetch_page_data, page): page for page in range(2, total_pages + 1)}
        for future in as_completed(futures):
            page_items, _ = future.result()
            items_to_get.extend(page_items)

    item_ids = [item['item_number'] for item in items_to_get]
    existing_items = SenitronItemAsset.objects.filter(item_number__in=item_ids)
    existing_items_ids = set(existing_items.values_list('item_number', flat=True))

    new_items = []
    items_to_update = []

    for item in items_to_get:
        new_item = create_inventory_item_asset_instance(logger, item)
        zoho_item = ZohoInventoryItem.objects.filter(item_id=new_item.item_number).first()
        sku_info = f"SKU: {zoho_item.sku}, " if zoho_item and zoho_item.sku else ''
        if new_item.item_number in existing_items_ids:
            items_to_update.append(new_item)
            prev_item = existing_items.get(item_number=new_item.item_number)
            if int(prev_item.status.senitron_id) != int(new_item.status.senitron_id):
                TimelineItem.objects.create(
                    item_number=new_item.item_number, 
                    previous_status_senitron=prev_item.status,
                    date_previous_status_senitron=prev_item.updated_at,
                    actual_status_senitron=new_item.status,
                    date_actual_status_senitron=new_item.last_seen if new_item.last_seen else new_item.updated_at,
                    zoho_item=zoho_item if zoho_item else None,
                    senitron_item=SenitronItem.objects.filter(item_number=new_item.item_number).first(),
                    text=f"Senitron Item ({sku_info}ID: {new_item.item_number}) senitron status changed from {prev_item.status.name} to {new_item.status.name}"
                ).save()
            if int(prev_item.senitron_item.qty) != int(new_item.senitron_item.qty):
                TimelineItem.objects.create(
                    item_number=new_item.item_number, 
                    previous_quantity=prev_item.senitron_item.qty,
                    date_previous_quantity=prev_item.updated_at,
                    actual_quantity=new_item.senitron_item.qty,
                    date_actual_quantity=new_item.last_seen if new_item.last_seen else new_item.updated_at,
                    zoho_item=zoho_item if zoho_item else None,
                    senitron_item=SenitronItem.objects.filter(item_number=new_item.item_number).first(),
                    text=f"Senitron Item ({sku_info}ID: {new_item.item_number}) quantity changed from {prev_item.senitron_item.qty} to {new_item.senitron_item.qty}"
                ).save()
        else:
            new_items.append(new_item)
            TimelineItem.objects.create(
                item_number=new_item.item_number, 
                date_previous_quantity=new_item.updated_at,
                date_actual_quantity=new_item.last_seen if new_item.last_seen else new_item.updated_at,
                date_previous_status_senitron=new_item.updated_at,
                date_actual_status_senitron=new_item.last_seen if new_item.last_seen else new_item.updated_at,
                zoho_item=zoho_item if zoho_item else None,
                senitron_item=SenitronItem.objects.filter(item_number=new_item.item_number).first(),
                text=f"Senitron Item (SKU: {zoho_item.sku or '-'}, ID: {new_item.item_number}, Qty: {new_item.senitron_item}, Status: {new_item.status.name}) created"
            ).save()
    
    with transaction.atomic():
        if new_items:
            SenitronItemAsset.objects.bulk_create(new_items, batch_size=200, ignore_conflicts=True)
        if items_to_update:
            SenitronItemAsset.objects.bulk_update(
                items_to_update,
                fields=[
                    'item_number',
                    'serial_number',
                    'alt_serial',
                    'first_seen',
                    'last_seen',
                    'last_seen_antenna',
                    'last_zone',
                    'handheld_reader',
                    'handheld_last_seen',
                    'static_zone',
                    'static_zone_last_update',
                    'receiving_date',
                    'current_units',
                    'storage_unit',
                    'adjust_qty',
                    'attr1',
                    'attr2',
                    'attr3',
                    'attr4',
                    'attr5',
                    'attr6',
                    'attr7',
                    'attr8',
                    'attr9',
                    'attr10',
                    'created_at',
                    'updated_at',
                    'epc',
                    'text3',
                    'status',
                    'senitron_item'
                ],
                batch_size=200
            )

    return JsonResponse({'message': 'Senitron Items Assets loaded successfully'}, status=200)


