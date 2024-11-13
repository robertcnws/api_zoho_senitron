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
from django.contrib.auth.models import User
from .models import AppConfig, ZohoInventoryItem, ZohoInventoryShipmentSalesOrder, LoginUser
from api_senitron.models import SenitronItem, TimelineItem
from .manage_instances import create_inventory_item_instance, create_inventory_sales_order_instance
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from datetime import datetime as dt
from concurrent.futures import as_completed, ThreadPoolExecutor
from django.contrib.auth import authenticate, login as auth_login
from django.forms.models import model_to_dict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
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
# CREATE USER
#############################################

@csrf_exempt
def manage_user(request, user_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = LoginUser.objects.create_user(
                username=data.get('username'),
                password=data.get('password'),
                first_name=data.get('firstName'),
                last_name=data.get('lastName'),
                email=data.get('email'),
                is_active=data.get('isActive') == 'active' or True,
                is_staff=data.get('role') == 'Admin' or False,
                is_superuser=data.get('is_superuser', False),
                phone_number=data.get('phoneNumber', None),
                country=data.get('country', None),
                state=data.get('state', None),
                city=data.get('city', None),
                address=data.get('address', None),
                zip_code=data.get('zipCode', None),
                gender=data.get('gender', None),                
            )
            user.set_password(data.get('password'))
            return JsonResponse({
                'data': model_to_dict(user)
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'description': 'Request is not in a valid format'}, status=400)
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            user = LoginUser.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            user.username = data.get('username', user.username)
            user.first_name = data.get('firstName', user.first_name)
            user.last_name = data.get('lastName', user.last_name)
            user.email = data.get('email', user.email)
            user.is_active = data.get('status') == 'active'
            user.is_staff = data.get('role') == 'Admin'
            user.is_superuser = data.get('isSuperuser', user.is_superuser)
            user.phone_number = data.get('phoneNumber', user.phone_number)
            user.country = data.get('country', user.country)
            user.state = data.get('state', user.state)
            user.city = data.get('city', user.city)
            user.address = data.get('address', user.address)
            user.zip_code = data.get('zipCode', user.zip_code)
            if data.get('password'):
                user.set_password(data.get('password'))
            user.save()
            return JsonResponse({
                'data': model_to_dict(user)
            }, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'description': 'Request is not in a valid format'}, status=400)
    elif request.method == 'DELETE':
        user = LoginUser.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)
        user.delete()
        return JsonResponse({'message': 'User deleted successfully'}, status=200)
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

MAX_WORKERS = 20

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_items(request):
    app_config = AppConfig.objects.first()
    logger.debug(f"AppConfig: {app_config}")

    try:
        headers = config_headers(request)
    except Exception as e:
        logger.error(f"Error connecting to Zoho API: {str(e)}")
        return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)

    data = json.loads(request.body) if request.body else {}
    item_number = data.get('item_number')

    if item_number:
        params = {
            'organization_id': app_config.zoho_org_id,
        }
        url = f"{settings.ZOHO_INVENTORY_ITEMS_URL}/{item_number}"
    else:
        params = {
            'organization_id': app_config.zoho_org_id,
            'per_page': 200,
            'page': 1
        }
        url = settings.ZOHO_INVENTORY_ITEMS_URL

    items_to_get = []

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)

    with requests.Session() as session:
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        def fetch_page(single_url, single_headers, single_params):
            try:
                response = session.get(single_url, headers=single_headers, params=single_params)
                if response.status_code == 401:
                    new_token = refresh_zoho_access_token()
                    single_headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                    response = session.get(single_url, headers=single_headers, params=single_params)
                response.raise_for_status()
                data = response.json()
                items = data.get('items', [])
                page_context = data.get('page_context', {})
                has_more_page = page_context.get('has_more_page', False)
                return items, has_more_page
            except requests.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                return [], False

        def fetch_single(single_url, single_headers, single_params):
            try:
                response = session.get(single_url, headers=single_headers, params=single_params)
                if response.status_code == 401:
                    new_token = refresh_zoho_access_token()
                    single_headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                    response = session.get(single_url, headers=single_headers, params=single_params)
                response.raise_for_status()
                data = response.json()
                return data.get('item', {})
            except requests.RequestException as e:
                logger.error(f"Error fetching single item: {e}")
                return {}

        if not item_number:
            page = 1
            has_more_page = True
            while has_more_page:
                current_params = params.copy()
                current_params['page'] = page
                page_items, has_more_page = fetch_page(url, headers.copy(), current_params)
                items_to_get.extend(page_items)
                page += 1
        else:
            single_item = fetch_single(url, headers.copy(), params.copy())
            if single_item:
                items_to_get.append(single_item)

    logger.debug(f"Total items fetched: {len(items_to_get)}")

    item_ids = [item['item_id'] for item in items_to_get]
    existing_items = ZohoInventoryItem.objects.filter(item_id__in=item_ids)
    existing_items_map = {item.item_id: item for item in existing_items}

    new_items = []
    items_to_update = []
    timeline_items = []

    for data_item in items_to_get:
        new_item = create_inventory_item_instance(logger, data_item)
        prev_item = existing_items_map.get(new_item.item_id)
        senitron_item = SenitronItem.objects.filter(item_number=new_item.item_id).first()

        if prev_item:
            items_to_update.append(new_item)

            if prev_item.status != new_item.status:
                timeline_items.append(
                    TimelineItem(
                        item_number=new_item.item_id,
                        previous_status_zoho=prev_item.status,
                        date_previous_status_zoho=prev_item.last_modified_time or prev_item.created_time,
                        actual_status_zoho=new_item.status,
                        date_actual_status_zoho=new_item.last_modified_time or new_item.created_time,
                        zoho_item=new_item,
                        senitron_item=senitron_item,
                        text=f"SKU: {new_item.sku or '-'} status changed from {prev_item.status} to {new_item.status}"
                    )
                )

            if int(prev_item.stock_on_hand) != int(new_item.stock_on_hand):
                timeline_items.append(
                    TimelineItem(
                        item_number=new_item.item_id,
                        previous_stock_on_hand=prev_item.stock_on_hand,
                        date_previous_stock_on_hand=prev_item.last_modified_time or prev_item.created_time,
                        actual_stock_on_hand=new_item.stock_on_hand,
                        date_actual_stock_on_hand=new_item.last_modified_time or new_item.created_time,
                        zoho_item=new_item,
                        senitron_item=senitron_item,
<<<<<<< HEAD
                        text=f"SKU: {new_item.sku or '-'} stock on hand changed from {int(prev_item.stock_on_hand)} to {int(new_item.stock_on_hand)}"
=======
                        text=f"SKU: {new_item.sku or '-'} (ID: {new_item.item_id}) stock on hand changed from {prev_item.stock_on_hand} to {new_item.stock_on_hand}"
>>>>>>> 59728d9a4d30ebe6067483c471a1d03414bd0d1c
                    )
                )
        else:
            new_items.append(new_item)
            timeline_items.append(
                TimelineItem(
                    item_number=new_item.item_id,
                    actual_stock_on_hand=new_item.stock_on_hand,
                    date_actual_stock_on_hand=new_item.last_modified_time or new_item.created_time,
                    actual_status_zoho=new_item.status,
                    date_actual_status_zoho=new_item.last_modified_time or new_item.created_time,
                    zoho_item=new_item,
                    senitron_item=senitron_item,
<<<<<<< HEAD
                    text=f"SKU: {new_item.sku or '-'} created with status {new_item.status}"
=======
                    text=f"SKU: {new_item.sku or '-'} (ID: {new_item.item_id}) created with status {new_item.status}"
>>>>>>> 59728d9a4d30ebe6067483c471a1d03414bd0d1c
                )
            )

    with transaction.atomic():
        if new_items:
            ZohoInventoryItem.objects.bulk_create(new_items, batch_size=200)
        if items_to_update:
            fields_to_update = [
                'status', 'stock_on_hand', 'last_modified_time'
            ]
            ZohoInventoryItem.objects.bulk_update(
                items_to_update,
                fields=fields_to_update,
                batch_size=200
            )
        if timeline_items:
            TimelineItem.objects.bulk_create(timeline_items, batch_size=200)

    logger.info(f"Items processed successfully: {len(new_items)} created, {len(items_to_update)} updated")
    return JsonResponse({'message': 'Items loaded successfully'}, status=200)
    

#############################################
# GET ALL INVENTORY SHIPMENT ORDERS
#############################################


def fetch_sales_order_details(item, session, headers):
    try:
        url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}/{item["salesorder_id"]}'
        response = session.get(url, headers=headers, params={})
        if response.status_code == 401:
            new_token = refresh_zoho_access_token()
            headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
            response = session.get(url, headers=headers, params={})
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
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date:
        return JsonResponse({'error': 'Date is missing'}, status=400)
    try:
        dt.strptime(start_date, '%Y-%m-%d')
        if end_date:
            dt.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    params = {
        'organization_id': app_config.zoho_org_id,
        'per_page': 200,
        'page': 1
    }
    if end_date:
        params.update({'date_start': start_date, 'date_end': end_date})
    else:
        params['date'] = start_date

    url = settings.ZOHO_INVENTORY_SALESORDERS_URL
    items_to_get = []
    session = requests.Session()

    while True:
        try:
            response = session.get(url, headers=headers, params=params)
            if response.status_code == 401:
                new_token = refresh_zoho_access_token()
                headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
                response = session.get(url, headers=headers, params=params)
            response.raise_for_status()
            items = response.json()
            items_to_get.extend(items.get('salesorders', []))
            if not items.get('page_context', {}).get('has_more_page', False):
                break
            params['page'] += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sales orders: {e}")
            return JsonResponse({'error': 'Failed to fetch sales orders'}, status=500)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_sales_order_details, item, session, headers) for item in items_to_get]
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
            ZohoInventoryShipmentSalesOrder.objects.bulk_create(new_sales_orders, ignore_conflicts=True, batch_size=200)
        if sales_orders_to_update:
            ZohoInventoryShipmentSalesOrder.objects.bulk_update(
                sales_orders_to_update,
                fields=[
                    'salesorder_number', 'date', 'status', 'customer_id', 'customer_name',
                    'is_taxable', 'tax_id', 'tax_name', 'tax_percentage', 'currency_id',
                    'currency_code', 'currency_symbol', 'exchange_rate', 'delivery_method',
                    'total_quantity', 'sub_total', 'tax_total', 'total', 'created_by_email',
                    'created_by_name', 'salesperson_id', 'salesperson_name', 'is_test_order',
                    'notes', 'payment_terms', 'payment_terms_label', 'line_items',
                    'shipping_address', 'billing_address', 'warehouses', 'custom_fields',
                    'order_sub_statuses', 'shipment_sub_statuses', 'created_time',
                    'last_modified_time'
                ],
                batch_size=200
            )
    return JsonResponse({'message': 'Sales Orders loaded successfully'}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny]) 
def sync_with_senitron(request):
    data = json.loads(request.body) if request.body else {}
    # print('Data', data)
    for item in data:
        try:
            zoho_item = ZohoInventoryItem.objects.filter(item_id=item['itemId']).first()
            zoho_item.synced_with_senitron = item['syncedWithSenitron']
            zoho_item.save()
        except ZohoInventoryItem.DoesNotExist:
            logger.error(f"Item {item['item_id']} not found in Zoho")
    return JsonResponse({'message': 'Items synced successfully'}, status=200)


   
    

#############################################
# EXTRA FUNCTIONS  
#############################################
