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
from .models import AppConfig, ZohoInventoryItem, ZohoInventoryShipmentSalesOrder
from .manage_instances import create_inventory_item_instance, create_inventory_sales_order_instance
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from datetime import datetime as dt
from concurrent.futures import as_completed, ThreadPoolExecutor
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.forms.models import model_to_dict
import logging



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#############################################
# ZOHO API TOKENS FUNCTIONS
#############################################
#############################################
# GENERATE AUTH URL
#############################################

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  
            username = data.get('username')  
            password = data.get('password') 
            if not username or not password:
                return JsonResponse({'error': 'Username and password required', 'description': 'Username and password required'}, status=400)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                logger.info(f'User {username} logged in')
                return JsonResponse({
                    'data': model_to_dict(user)
                }, status=200)
            login_user = User.objects.filter(username=username).first()
            if login_user:
                return JsonResponse({'error': 'Invalid credentials', 'description' : 'Incorrect Password'}, status=400)
            else:
                return JsonResponse({'error': 'Invalid credentials', 'description' : 'Username does not exist'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'description': 'Request is not in a valid format'}, status=400)
    return JsonResponse({'error': 'Method not allowed', 'description': 'Method not allowed'}, status=405)


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

MAX_WORKERS = 10 

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_items(request):
    app_config = AppConfig.objects.first()
    logger.debug(app_config)

    try:
        headers = config_headers(request)
    except Exception as e:
        logger.error(f"Error connecting to Zoho API: {str(e)}")
        return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)
    
    params = {
        'organization_id': app_config.zoho_org_id,
        'page': 1,
        'per_page': 200,
    }

    url = f'{settings.ZOHO_INVENTORY_ITEMS_URL}'
    items_to_get = []

    def fetch_page_data(page):
        try:
            params['page'] = page
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:
                new_token = refresh_zoho_access_token()
                headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            items = response.json()
            return items.get('items', [])
        except requests.RequestException as e:
            logger.error(f"Error fetching items for page {page}: {e}")
            return []
    
    has_more_pages = True
    page = 1
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(fetch_page_data, page): page}
        while has_more_pages:
            future = as_completed(future_to_page)
            for f in future:
                page_items = f.result()
                if page_items:
                    items_to_get.extend(page_items)
                else:
                    has_more_pages = False
                page += 1
                future_to_page[executor.submit(fetch_page_data, page)] = page
    
    item_ids = [item['item_id'] for item in items_to_get]
    existing_items = ZohoInventoryItem.objects.filter(item_id__in=item_ids)
    existing_items_ids = set(existing_items.values_list('item_id', flat=True))

    new_items = []
    items_to_update = []

    for data in items_to_get:
        new_item = create_inventory_item_instance(logger, data)
        if new_item.item_id in existing_items_ids:
            items_to_update.append(new_item)
        else:
            new_items.append(new_item)
    
    with transaction.atomic():
        if new_items:
            ZohoInventoryItem.objects.bulk_create(
                new_items, batch_size=100, ignore_conflicts=True
            )

        if items_to_update:
            ZohoInventoryItem.objects.bulk_update(
                items_to_update,
                fields=[
                    'group_id', 
                    'group_name', 
                    'name', 
                    'status', 
                    'source', 
                    'is_linked_with_zohocrm',
                    'item_type', 
                    'description', 
                    'rate', 
                    'is_taxable', 
                    'tax_id', 
                    'tax_name', 
                    'tax_percentage',
                    'purchase_description', 
                    'purchase_rate', 
                    'is_combo_product', 
                    'product_type', 
                    'attribute_id1',
                    'attribute_name1', 
                    'reorder_level', 
                    'stock_on_hand', 
                    'available_stock', 
                    'actual_available_stock',
                    'sku', 
                    'upc', 
                    'ean', 
                    'isbn', 
                    'part_number', 
                    'attribute_option_id1', 
                    'attribute_option_name1',
                    'image_name', 
                    'image_type', 
                    'created_time', 
                    'last_modified_time', 
                    'hsn_or_sac',
                    'sat_item_key_code', 
                    'unitkey_code'
                ],
                batch_size=100
            )

    return JsonResponse({'message': 'Items loaded successfully'}, status=200)
    
    

#############################################
# GET ALL INVENTORY SHIPMENT ORDERS
#############################################


def fetch_sales_order_details(item, headers, params):
    try:
        url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}/{item["salesorder_id"]}'
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 401:
            new_token = refresh_zoho_access_token()
            headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
            response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        full_item = response.json()
        return full_item.get('salesorder', None)
    except Exception as e:
        logger.error(f"Error fetching details for sales order {item['salesorder_id']}: {e}")
        return None

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_sales_orders(request):
    
    app_config = AppConfig.objects.first()
    logger.debug(app_config)
    try:
        headers = config_headers(request)
    except Exception as e:
        logger.error(f"Error connecting to Zoho API: {str(e)}")
        return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)

    data = json.loads(request.body)
    start_date = data.get('start_date', None)
    end_date = data.get('end_date', None)

    if not start_date:
        return JsonResponse({'error': 'Date is missing'}, status=400)
    try:
        dt.strptime(start_date, '%Y-%m-%d')
        if end_date:
            dt.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    if not end_date:
        params = {
            'organization_id': app_config.zoho_org_id,
            'date': start_date,
            'page': 1,
            'per_page': 200,
        }
    else:
        params = {
            'organization_id': app_config.zoho_org_id,
            'date_start': start_date,
            'date_end': end_date,
            'page': 1,
            'per_page': 200,
        }
    url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}'
    items_to_get = []

    while True:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:
                new_token = refresh_zoho_access_token()
                headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            items = response.json()
            items_to_get.extend(items.get('salesorders', []))
            if not items.get('page_context', {}).get('has_more_page', False):
                break
            params['page'] += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sales orders: {e}")
            return JsonResponse({'error': 'Failed to fetch sales orders'}, status=500)
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_sales_order_details, item, headers, params) for item in items_to_get]
        full_items_to_get = [future.result() for future in as_completed(futures) if future.result()]
    
    salesorder_ids = [item['salesorder_id'] for item in full_items_to_get]
    existing_orders = ZohoInventoryShipmentSalesOrder.objects.filter(salesorder_id__in=salesorder_ids)
    existing_salesorder_ids = set(existing_orders.values_list('salesorder_id', flat=True))

    new_sales_orders = []
    sales_orders_to_update = []
    
    for data in full_items_to_get:
        new_item = create_inventory_sales_order_instance(logger, data)
        if new_item.salesorder_id in existing_salesorder_ids:
            sales_orders_to_update.append(new_item)
        else:
            new_sales_orders.append(new_item)

    with transaction.atomic():
        if new_sales_orders:
            ZohoInventoryShipmentSalesOrder.objects.bulk_create(new_sales_orders, ignore_conflicts=True)
            
        if sales_orders_to_update:
            ZohoInventoryShipmentSalesOrder.objects.bulk_update(
                sales_orders_to_update,
                fields=[
                    'salesorder_number',
                    'date',
                    'status',
                    'customer_id',
                    'customer_name',
                    'is_taxable',
                    'tax_id',
                    'tax_name',
                    'tax_percentage',
                    'currency_id',
                    'currency_code',
                    'currency_symbol',
                    'exchange_rate',
                    'delivery_method',
                    'total_quantity',
                    'sub_total',
                    'tax_total',
                    'total',
                    'created_by_email',
                    'created_by_name',
                    'salesperson_id',
                    'salesperson_name',
                    'is_test_order',
                    'notes',
                    'payment_terms',
                    'payment_terms_label',
                    'line_items',
                    'shipping_address',
                    'billing_address',
                    'warehouses',
                    'custom_fields',
                    'order_sub_statuses',
                    'shipment_sub_statuses',
                    'created_time',
                    'last_modified_time',
                ]
            )
        

    return JsonResponse({'message': 'Sales Orders loaded successfully'}, status=200)

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def load_inventory_sales_orders(request):
#     # username = request.data.get('username', '')
#     app_config = AppConfig.objects.first()
#     logger.debug(app_config)
#     try:
#         headers = config_headers(request)  
#     except Exception as e:
#         logger.error(f"Error connecting to Zoho API: {str(e)}")
#         return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)
    
#     data = json.loads(request.body)
    
#     date = data.get('date', None)
    
#     if not date:
#         return JsonResponse({'error': 'Date is missing'}, status=400)
#     elif not isinstance(date, str):
#         return JsonResponse({'error': 'Invalid date format'}, status=400)
#     elif not dt.strptime(date, '%Y-%m-%d'):
#         return JsonResponse({'error': 'Invalid date'}, status=400)
        
#     params = {
#         'organization_id': app_config.zoho_org_id,
#         'date': date,
#         'page': 1,       
#         'per_page': 200,  
#     }
        
#     url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}'
#     values_from_json = 'salesorders'
#     items_to_get = []
#     full_items_to_get = []
        
#     while True:
#         try:
#             response = requests.get(url, headers=headers, params=params)
#             if response.status_code == 401:  
#                 new_token = refresh_zoho_access_token()
#                 headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#                 response = requests.get(url, headers=headers, params=params)  
#             elif response.status_code != 200:
#                 logger.error(f"Error fetching items: {response.text}")
#                 return JsonResponse({'error': response.text}, status=response.status_code)
#             else:
#                 response.raise_for_status()
#                 items = response.json()
#                 if items.get(values_from_json, []):
#                     items_to_get.extend(items[values_from_json])
#                 if 'page_context' in items and 'has_more_page' in items['page_context'] and items['page_context']['has_more_page']:
#                     params['page'] += 1  
#                 else:
#                     break  
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Error fetching sales orders: {e}")
#             return JsonResponse({'error': 'Failed to fetch sales orders'}, status=500)
    
#     for item in items_to_get:
#         url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}/{item["salesorder_id"]}'
#         try:
#             response = requests.get(url, headers=headers, params=params)
#             if response.status_code == 401:  
#                 new_token = refresh_zoho_access_token()
#                 headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#                 response = requests.get(url, headers=headers, params=params)  
#             elif response.status_code != 200:
#                 logger.error(f"Error fetching items: {response.text}")
#                 return JsonResponse({'error': response.text}, status=response.status_code)
#             else:
#                 response.raise_for_status()
#                 full_item = response.json()
#                 if full_item.get('salesorder', {}):
#                     full_items_to_get.append(full_item['salesorder'])
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Error fetching details sale order: {e}")
#             return JsonResponse({'error': 'Failed to fetch detail sale order'}, status=500)
        
#     with transaction.atomic():
#         for data in full_items_to_get:
#             new_item = create_inventory_sales_order_instance(data)
#             duplicates = ZohoInventorySalesOrder.objects.filter(salesorder_id=new_item.salesorder_id)
#             if duplicates.count() > 1:
#                 duplicates.exclude(id=duplicates.first().id).delete()
#             ZohoInventorySalesOrder.objects.update_or_create(
#                 salesorder_id=new_item.salesorder_id,
#                 defaults={
#                     'salesorder_number': new_item.salesorder_number,
#                     'date': new_item.date,
#                     'status': new_item.status,
#                     'customer_id': new_item.customer_id,
#                     'customer_name': new_item.customer_name,
#                     'is_taxable': new_item.is_taxable,
#                     'tax_id': new_item.tax_id,
#                     'tax_name': new_item.tax_name,
#                     'tax_percentage': new_item.tax_percentage,
#                     'currency_id': new_item.currency_id,
#                     'currency_code': new_item.currency_code,
#                     'currency_symbol': new_item.currency_symbol,
#                     'exchange_rate': new_item.exchange_rate,
#                     'delivery_method': new_item.delivery_method,
#                     'total_quantity': new_item.total_quantity,
#                     'sub_total': new_item.sub_total,
#                     'tax_total': new_item.tax_total,
#                     'total': new_item.total,
#                     'created_by_email': new_item.created_by_email,
#                     'created_by_name': new_item.created_by_name,
#                     'salesperson_id': new_item.salesperson_id,
#                     'salesperson_name': new_item.salesperson_name,
#                     'is_test_order': new_item.is_test_order,
#                     'notes': new_item.notes,
#                     'payment_terms': new_item.payment_terms,
#                     'payment_terms_label': new_item.payment_terms_label,
#                     'line_items': new_item.line_items,
#                     'shipping_address': new_item.shipping_address,
#                     'billing_address': new_item.billing_address,
#                     'warehouses': new_item.warehouses,
#                     'custom_fields': new_item.custom_fields,
#                     'order_sub_statuses': new_item.order_sub_statuses,
#                     'shipment_sub_statuses': new_item.shipment_sub_statuses,
#                     'created_time': new_item.created_time,
#                     'last_modified_time': new_item.last_modified_time,
#                 }
#             )
                
#     return JsonResponse({'message': 'Sales Orders loaded successfully'}, status=200)
    
    

#############################################
# EXTRA FUNCTIONS  
#############################################
