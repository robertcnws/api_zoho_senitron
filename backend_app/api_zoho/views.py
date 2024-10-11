from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import requests
import json
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import AppConfig, ZohoInventoryItem
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from datetime import datetime as dt
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


#############################################
# ZOHO API TOKENS FUNCTIONS
#############################################
#############################################
# GENERATE AUTH URL
#############################################

@api_view(['GET'])
@permission_classes([AllowAny])
def generate_auth_url(request):
    app_config = AppConfig.objects.first()
    client_id = app_config.zoho_client_id
    redirect_uri = app_config.zoho_redirect_uri
    scopes = ",".join(settings.ZOHO_SCOPES)
    auth_url = f"https://accounts.zoho.com/oauth/v2/auth?scope={scopes}&client_id={client_id}&response_type=code&access_type=offline&redirect_uri={redirect_uri}"
    return JsonResponse({'auth_url': auth_url}, status=200)


#############################################
# GET ACCESS TOKEN
#############################################

def get_access_token(client_id, client_secret, refresh_token):
    logger.info('Getting access token')
    token_url = "https://accounts.zoho.com/oauth/v2/token"
    if not refresh_token:
        raise Exception("Refresh token is missing")
        # refresh_token = get_refresh_token()
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        access_token = response.json()["access_token"]
    else:
        raise Exception("Error retrieving access token")
    return access_token


#############################################
# REFRESH ZOHO ACCESS TOKEN
#############################################

def refresh_zoho_access_token():
    app_config = AppConfig.objects.first()
    refresh_url = "https://accounts.zoho.com/oauth/v2/token"
    payload = {
        'refresh_token': app_config.zoho_refresh_token,
        'client_id': app_config.zoho_client_id,
        'client_secret': app_config.zoho_client_secret,
        'grant_type': 'refresh_token'
    }
    response = requests.post(refresh_url, data=payload)
    if response.status_code == 200:
        new_token = response.json().get('access_token')
        return new_token
    else:
        raise Exception("Failed to refresh Zoho token")


#############################################
# GET REFRESH TOKEN
#############################################

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_refresh_token(request):
    authorization_code = request.GET.get("code", None)
    if not authorization_code:
        return JsonResponse({'error': 'Authorization code is missing'}, status=400)
    
    app_config = AppConfig.objects.first()
    token_url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "code": authorization_code,
        "client_id": app_config.zoho_client_id,
        "client_secret": app_config.zoho_client_secret,
        "redirect_uri": app_config.zoho_redirect_uri,
        "grant_type": "authorization_code",
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        response_json = response.json()
        access_token = response_json.get("access_token", None)
        refresh_token = response_json.get("refresh_token", None)

        if access_token and refresh_token:
            app_config.zoho_refresh_token = refresh_token
            app_config.save()
            return redirect(f'{settings.FRONTEND_URL}/integration')
        else:
            return JsonResponse({'error': 'Failed to obtain access_token and/or refresh_token'}, status=400)

    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


#############################################
# ZOHO API SETTINGS
#############################################

@api_view(['GET'])
@permission_classes([AllowAny])
def zoho_api_settings(request):
    app_config = AppConfig.objects.first()
    if not app_config:
        app_config = AppConfig.objects.create()

    connected = (
        app_config.zoho_connection_configured
        and app_config.zoho_refresh_token is not None
        or ""
    )
    auth_url = None
    if not connected:
        auth_url = reverse("api_zoho:generate_auth_url")
    app_config_json = serializers.serialize('json', [app_config])
    app_config_data = json.loads(app_config_json)[0]['fields']
    data = {
            "app_config": app_config_data,
            "connected": connected,
            "auth_url": auth_url,
            "zoho_connection_configured": app_config.zoho_connection_configured,
    }
    return JsonResponse(data, status=200)


#############################################
# ZOHO API CONNECT
#############################################

@login_required(login_url='login')
def zoho_api_connect(request):
    app_config = AppConfig.objects.first()
    if app_config.zoho_connection_configured:
        try:
            get_access_token(
                app_config.zoho_client_id,
                app_config.zoho_client_secret,
                app_config.zoho_refresh_token,
            )
            messages.success(request, "Zoho API connected successfully.")
        except Exception as e:
            messages.error(request, f"Error connecting to Zoho API: {str(e)}")
    else:
        messages.warning(request, "Zoho API connection is not configured yet.")
    return JsonResponse({'message': 'Zoho API connected successfully.'}, status=200)
    

#############################################
# CONFIG HEADERS
#############################################

def config_headers(request):
    app_config = AppConfig.objects.first()
    access_token = get_access_token(
        app_config.zoho_client_id,
        app_config.zoho_client_secret,
        app_config.zoho_refresh_token,
    )
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    return headers


#############################################
# LOAD FROM ZOHO FUNCTIONS
#############################################
#############################################
# GET ALL INVENTORY ITEMS
#############################################

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_items(request):
    # username = request.data.get('username', '')
    app_config = AppConfig.objects.first()
    logger.debug(app_config)
    try:
        headers = config_headers(request)  # Asegúrate de que esto esté configurado correctamente
    except Exception as e:
        logger.error(f"Error connecting to Zoho API: {str(e)}")
        return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)
        
    items_saved = list(ZohoInventoryItem.objects.all())
        
    params = {
        'organization_id': app_config.zoho_org_id,
        'page': 1,       
        'per_page': 200,  
    }
        
    url = f'{settings.ZOHO_INVENTORY_ITEMS_URL}'
    items_to_save = []
    items_to_get = []
        
    while True:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:  
                new_token = refresh_zoho_access_token()
                headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                response = requests.get(url, headers=headers, params=params)  
            elif response.status_code != 200:
                logger.error(f"Error fetching items: {response.text}")
                return JsonResponse({'error': response.text}, status=response.status_code)
            else:
                response.raise_for_status()
                items = response.json()
                if items.get('items', []):
                    items_to_get.extend(items['items'])
                if 'page_context' in items and 'has_more_page' in items['page_context'] and items['page_context']['has_more_page']:
                    params['page'] += 1  
                else:
                    break  
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching items: {e}")
            return JsonResponse({'error': 'Failed to fetch items'}, status=500)
        
    existing_item_ids = ZohoInventoryItem.objects.filter(item_id__in=[item['item_id'] for item in items_to_get]).values_list('item_id', flat=True)
    
    new_items = [create_inventory_item_instance(data) for data in items_to_get if data['item_id'] not in existing_item_ids]

    with transaction.atomic():
        ZohoInventoryItem.objects.bulk_create(new_items)
                
    return JsonResponse({'message': 'Items loaded successfully'}, status=200)
    
    

#############################################
# GET ALL INVENTORY SHIPMENT ORDERS
#############################################

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_shipment_orders(request):
    # username = request.data.get('username', '')
    app_config = AppConfig.objects.first()
    logger.debug(app_config)
    try:
        headers = config_headers(request)  # Asegúrate de que esto esté configurado correctamente
    except Exception as e:
        logger.error(f"Error connecting to Zoho API: {str(e)}")
        return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)
        
    # items_saved = list(ZohoInventoryItem.objects.all())
        
    params = {
        'organization_id': app_config.zoho_org_id,
        'date': dt.now().strftime('%Y-%m-%d'),
        'page': 1,       
        'per_page': 200,  
    }
        
    url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}'
    values_from_json = 'salesorders'
    # url = f'{settings.ZOHO_INVENTORY_SHIPMENTORDERS_URL}'
    # values_from_json = 'shipmentorders'
    items_to_save = []
    items_to_get = []
    full_items_to_get = []
        
    while True:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:  
                new_token = refresh_zoho_access_token()
                headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                response = requests.get(url, headers=headers, params=params)  
            elif response.status_code != 200:
                logger.error(f"Error fetching items: {response.text}")
                return JsonResponse({'error': response.text}, status=response.status_code)
            else:
                response.raise_for_status()
                items = response.json()
                if items.get(values_from_json, []):
                    items_to_get.extend(items[values_from_json])
                if 'page_context' in items and 'has_more_page' in items['page_context'] and items['page_context']['has_more_page']:
                    params['page'] += 1  
                else:
                    break  
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sales orders: {e}")
            return JsonResponse({'error': 'Failed to fetch sales orders'}, status=500)
    
    for item in items_to_get:
        url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}/{item["salesorder_id"]}'
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:  
                new_token = refresh_zoho_access_token()
                headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                response = requests.get(url, headers=headers, params=params)  
            elif response.status_code != 200:
                logger.error(f"Error fetching items: {response.text}")
                return JsonResponse({'error': response.text}, status=response.status_code)
            else:
                response.raise_for_status()
                full_item = response.json()
                if full_item.get('salesorder', []):
                    full_items_to_get.extend(full_item['salesorder'])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching details sale order: {e}")
            return JsonResponse({'error': 'Failed to fetch detail sale order'}, status=500)
        
    print(full_items_to_get)
        
        # existing_items = {item.item_id: item for item in items_saved}

        # for data in items_to_get:
        #     new_item = create_inventory_item_instance(data)
        #     if new_item.item_id not in existing_items:
        #         items_to_save.append(new_item)
        
        # def save_items_in_batches(items, batch_size=100):
        #     for i in range(0, len(items), batch_size):
        #         batch = items[i:i + batch_size]
        #         with transaction.atomic():
        #             ZohoInventoryItem.objects.bulk_create(batch)
        
        # save_items_in_batches(items_to_save, batch_size=100)
                
    return JsonResponse({'message': 'Items loaded successfully'}, status=200)
    
    

#############################################
# EXTRA FUNCTIONS  
#############################################
#############################################
# CREATE INVENTORY INSTANCE
#############################################

def create_inventory_item_instance(data):
    
    created_time_str = data.get('created_time', None)
    created_time = dt.strptime(created_time_str, '%Y-%m-%dT%H:%M:%S%z').date() if created_time_str else None
    
    last_modified_time_str = data.get('last_modified_time', None)
    last_modified_time = dt.strptime(last_modified_time_str, '%Y-%m-%dT%H:%M:%S%z').date() if last_modified_time_str else None
    
    new_item = ZohoInventoryItem.objects.create(
        group_id=data.get('group_id', 0),
        group_name=data.get('group_name', ''),
        item_id=data.get('item_id', 0),
        name=data.get('name', ''),
        status=data.get('status', ''),
        source=data.get('source', ''),
        is_linked_with_zohocrm=data.get('is_linked_with_zohocrm', False),
        item_type=data.get('item_type', ''),
        description=data.get('description', ''),
        rate=data.get('rate', 0),
        is_taxable=data.get('is_taxable', False),
        tax_id=data.get('tax_id') if isinstance(data.get('tax_id'), (int, float)) else 0,
        tax_name=data.get('tax_name', ''),
        tax_percentage=data.get('tax_percentage', 0),
        purchase_description=data.get('purchase_description', ''),
        purchase_rate=data.get('purchase_rate', 0),
        is_combo_product=data.get('is_combo_product', False),
        product_type=data.get('product_type', ''),
        attribute_id1=data.get('attribute_id1') if isinstance(data.get('attribute_id1'), (int, float)) else 0,
        attribute_name1=data.get('attribute_name1', ''),
        reorder_level=data.get('reorder_level') if isinstance(data.get('reorder_level'), (int, float)) else 0,
        stock_on_hand=data.get('stock_on_hand', 0),
        available_stock=data.get('available_stock', 0),
        actual_available_stock=data.get('actual_available_stock', 0),
        sku=data.get('sku', ''),
        upc=data.get('upc') if isinstance(data.get('upc'), (int, float)) else 0,
        ean=data.get('ean') if isinstance(data.get('ean'), (int, float)) else 0,
        isbn=data.get('isbn') if isinstance(data.get('isbn'), (int, float)) else 0,
        part_number=data.get('part_number') if isinstance(data.get('part_number'), (int, float)) else 0,
        attribute_option_id1=data.get('attribute_option_id1') if isinstance(data.get('attribute_option_id1'), (int, float)) else 0,
        attribute_option_name1=data.get('attribute_option_name1', ''),
        image_name=data.get('image_name', ''),
        image_type=data.get('image_type', ''),
        created_time=created_time,
        last_modified_time=last_modified_time,
        hsn_or_sac=data.get('hsn_or_sac') if isinstance(data.get('hsn_or_sac'), (int, float)) else 0,
        sat_item_key_code=data.get('sat_item_key_code', ''),
        unitkey_code=data.get('unitkey_code', '')
    )

    return new_item