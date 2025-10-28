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
from django.db.models import Max
from .models import (
                    AppConfig, 
                    ZohoInventoryItem, 
                    ZohoInventoryShipmentSalesOrder, 
                    LoginUser, 
                    ZohoSkuTrackInfo, 
                    ZohoShipmentOrder, 
                    ZohoPackage, 
                    ZohoItemAssetsTrack, 
                    JobsUpdatingTimes, 
                    ManualUpdatingJobs
                )
from api_senitron.models import SenitronItem, TimelineItem
from api_senitron.views import create_notification
from .manage_instances import (
                              create_inventory_item_instance,
                              create_inventory_sales_order_instance,
                              create_inventory_shipment_instance, 
                              create_inventory_package_instance, 
                              create_zoho_item_assets_track_instance
                            )
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from datetime import datetime as dt
from concurrent.futures import as_completed, ThreadPoolExecutor
from django.contrib.auth import authenticate, login as auth_login
from django.forms.models import model_to_dict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api_zoho.auth_serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer
from .services_from_main_load import (
    sync_inventory_items, sync_inventory_sales_orders, sync_inventory_shipments
)
from .services_from_zoho import (
    get_access_token,
    refresh_zoho_access_token,
)
import logging
import time
import utils.authorization_utils as auth_utils

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
    

def health(request):
    return JsonResponse({"status": "ok"})

#############################################
# ZOHO API TOKENS FUNCTIONS
#############################################
#############################################
# GENERATE AUTH URL
#############################################

@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def health_check(request):
    logger.info('Health check endpoint called')
    return JsonResponse({'status': 'ok'}, status=200)

#############################################
# LOGIN
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
                    'data': model_to_dict(user),
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
            payload_username = data.get('manager_username')
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
            if payload_username:
                module='create_system_user'
                info=f'has created new user: {user.username}'
                type='create_system_user'
                create_notification(module, info, type, payload_username)
            return JsonResponse({
                'data': model_to_dict(user)
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'description': 'Request is not in a valid format'}, status=400)
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            payload_username = data.get('manager_username')
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
            if payload_username:
                module='update_system_user'
                info=f'has updated user: {user.username}'
                type='update_system_user'
                create_notification(module, info, type, payload_username)
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
# LOAD FROM ZOHO FUNCTIONS
#############################################
#############################################
# GET ALL INVENTORY ITEMS
#############################################

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def load_inventory_items(request):
#     app_config = AppConfig.objects.first()
#     logger.debug(f"AppConfig: {app_config}")

#     try:
#         headers = config_headers()
#     except Exception as e:
#         logger.error(f"Error connecting to Zoho API: {str(e)}")
#         return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)

#     data = json.loads(request.body) if request.body else {}
#     item_number = data.get('item_number')
#     username = data.get('username', None)

#     if item_number:
#         params = {
#             'organization_id': app_config.zoho_org_id,
#         }
#         url = f"{settings.ZOHO_INVENTORY_ITEMS_URL}/{item_number}"
#     else:
#         params = {
#             'organization_id': app_config.zoho_org_id,
#             'per_page': 200,
#             'page': 1
#         }
#         url = settings.ZOHO_INVENTORY_ITEMS_URL

#     items_to_get = []

#     retry_strategy = Retry(
#         total=3,
#         status_forcelist=[429, 500, 502, 503, 504],
#         allowed_methods=["GET", "POST"]
#     )
#     adapter = HTTPAdapter(max_retries=retry_strategy)

#     with requests.Session() as session:
#         session.mount("https://", adapter)
#         session.mount("http://", adapter)

#         def fetch_page(single_url, single_headers, single_params):
#             try:
#                 response = session.get(single_url, headers=single_headers, params=single_params)
#                 if response.status_code == 401:
#                     new_token = refresh_zoho_access_token()
#                     single_headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#                     response = session.get(single_url, headers=single_headers, params=single_params)
#                 response.raise_for_status()
#                 data = response.json()
#                 items = data.get('items', [])
#                 page_context = data.get('page_context', {})
#                 has_more_page = page_context.get('has_more_page', False)
#                 return items, has_more_page
#             except requests.RequestException as e:
#                 logger.error(f"Error fetching data: {e}")
#                 return [], False

#         def fetch_single(single_url, single_headers, single_params):
#             try:
#                 response = session.get(single_url, headers=single_headers, params=single_params)
#                 if response.status_code == 401:
#                     new_token = refresh_zoho_access_token()
#                     single_headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#                     response = session.get(single_url, headers=single_headers, params=single_params)
#                 response.raise_for_status()
#                 data = response.json()
#                 return data.get('item', {})
#             except requests.RequestException as e:
#                 logger.error(f"Error fetching single item: {e}")
#                 return {}

#         if not item_number:
#             page = 1
#             has_more_page = True
#             while has_more_page:
#                 current_params = params.copy()
#                 current_params['page'] = page
#                 page_items, has_more_page = fetch_page(url, headers.copy(), current_params)
#                 items_to_get.extend(page_items)
#                 page += 1
#         else:
#             single_item = fetch_single(url, headers.copy(), params.copy())
#             if single_item:
#                 items_to_get.append(single_item)

#     logger.debug(f"Total items fetched: {len(items_to_get)}")

#     item_ids = [item['item_id'] for item in items_to_get]
#     existing_items = ZohoInventoryItem.objects.filter(item_id__in=item_ids)
#     existing_items_map = {item.item_id: item for item in existing_items}

#     new_items = []
#     items_to_update = []
#     timeline_items = []

#     for data_item in items_to_get:
#         new_item = create_inventory_item_instance(logger, data_item)
#         prev_item = existing_items_map.get(new_item.item_id)
#         senitron_item = SenitronItem.objects.filter(item_number=new_item.item_id).first()

#         if prev_item:
#             items_to_update.append(new_item)

#             if prev_item.status != new_item.status:
#                 timeline_items.append(
#                     TimelineItem(
#                         item_number=new_item.item_id,
#                         previous_status_zoho=prev_item.status,
#                         date_previous_status_zoho=prev_item.last_modified_time or prev_item.created_time,
#                         actual_status_zoho=new_item.status,
#                         date_actual_status_zoho=new_item.last_modified_time or new_item.created_time,
#                         zoho_item=new_item,
#                         senitron_item=senitron_item,
#                         text=f"{new_item.sku or '-'} status changed -> From {prev_item.status} to {new_item.status}"
#                     )
#                 )

#             if int(prev_item.stock_on_hand) != int(new_item.stock_on_hand):
#                 change = 'added' if new_item.stock_on_hand > prev_item.stock_on_hand else 'removed'
#                 abs_value = abs(new_item.stock_on_hand - prev_item.stock_on_hand)
#                 timeline_items.append(
#                     TimelineItem(
#                         item_number=new_item.item_id,
#                         previous_stock_on_hand=prev_item.stock_on_hand,
#                         date_previous_stock_on_hand=prev_item.last_modified_time or prev_item.created_time,
#                         actual_stock_on_hand=new_item.stock_on_hand,
#                         date_actual_stock_on_hand=new_item.last_modified_time or new_item.created_time,
#                         zoho_item=new_item,
#                         senitron_item=senitron_item,
#                         text=f"{new_item.sku or '-'} : {int(abs_value)} unit(s) {change} -> New stock on hand: {int(new_item.stock_on_hand)}"
#                     )
#                 )
#         else:
#             new_items.append(new_item)
#             timeline_items.append(
#                 TimelineItem(
#                     item_number=new_item.item_id,
#                     actual_stock_on_hand=new_item.stock_on_hand,
#                     date_actual_stock_on_hand=new_item.last_modified_time or new_item.created_time,
#                     actual_status_zoho=new_item.status,
#                     date_actual_status_zoho=new_item.last_modified_time or new_item.created_time,
#                     zoho_item=new_item,
#                     senitron_item=senitron_item,
#                     text=f"{new_item.sku or '-'} created -> On hand: {int(new_item.stock_on_hand)}, Status: {new_item.status}"
#                 )
#             )

#     with transaction.atomic():
#         if new_items:
#             ZohoInventoryItem.objects.bulk_create(new_items, batch_size=200, ignore_conflicts=True)
#         if items_to_update:
#             fields_to_update = [
#                 'status', 'stock_on_hand', 'last_modified_time'
#             ]
#             ZohoInventoryItem.objects.bulk_update(
#                 items_to_update,
#                 fields=fields_to_update,
#                 batch_size=200
#             )
#         if timeline_items:
#             TimelineItem.objects.bulk_create(timeline_items, batch_size=200, ignore_conflicts=True)
            
#     previous_day = timezone.now()
            
#     JobsUpdatingTimes.objects.filter(last_updated__lt=previous_day).delete()
            
#     JobsUpdatingTimes.objects.create(last_updated=timezone.now())

#     logger.info(f"Items processed successfully: {len(new_items)} created, {len(items_to_update)} updated")
    
#     if username:
#         module='zoho_item'
#         info='has loaded new info from Zoho Items'
#         type='load'
#         create_notification(module, info, type, username)
    
#         module='system_timeline'
#         info='has added new info about timelines in Zoho Items'
#         type='create_timeline'
#         create_notification(module, info, type, username)
    
#     return JsonResponse({'message': 'Items loaded successfully'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_items(request):
    data = json.loads(request.body) if request.body else {}
    username = data.get('username')
    out = sync_inventory_items()
    if username:
        module='zoho_item'
        info='has loaded new info from Zoho Items'
        type='load'
        create_notification(module, info, type, username)
    
        module='system_timeline'
        info='has added new info about timelines in Zoho Items'
        type='create_timeline'
        create_notification(module, info, type, username)
    return JsonResponse({'message': 'Items loaded successfully', **out}, status=200)
    

#############################################
# GET ALL INVENTORY SHIPMENT ORDERS
#############################################


# def fetch_sales_order_details(item, session, headers):
#     try:
#         url = f'{settings.ZOHO_INVENTORY_SALESORDERS_URL}/{item["salesorder_id"]}'
#         response = session.get(url, headers=headers, params={})
#         if response.status_code == 401:
#             new_token = refresh_zoho_access_token()
#             headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#             response = session.get(url, headers=headers, params={})
#         response.raise_for_status()
#         full_item = response.json()
#         return full_item.get('salesorder', None)
#     except Exception as e:
#         logger.error(f"Error fetching details for sales order {item['salesorder_id']}: {e}")
#         return None
    

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def load_inventory_sales_orders(request):
#     MAX_WORKERS = 10
#     app_config = AppConfig.objects.first()
#     logger.debug(app_config)
#     try:
#         headers = config_headers()
#     except Exception as e:
#         logger.error(f"Error connecting to Zoho API: {str(e)}")
#         return JsonResponse({'error': f"Error connecting to Zoho API (Load Items): {str(e)}"}, status=500)

#     data = json.loads(request.body)
#     start_date = data.get('start_date')
#     end_date = data.get('end_date')
#     username = data.get('username', None)

#     if not start_date:
#         return JsonResponse({'error': 'Date is missing'}, status=400)
#     try:
#         dt.strptime(start_date, '%Y-%m-%d')
#         if end_date:
#             dt.strptime(end_date, '%Y-%m-%d')
#     except ValueError:
#         return JsonResponse({'error': 'Invalid date format'}, status=400)
    
#     params = {
#         'organization_id': app_config.zoho_org_id,
#         'per_page': 200,
#         'page': 1
#     }
#     if end_date:
#         params.update({'date_start': start_date, 'date_end': end_date})
#     else:
#         params['date'] = start_date

#     url = settings.ZOHO_INVENTORY_SALESORDERS_URL
#     items_to_get = []
#     session = requests.Session()

#     while True:
#         try:
#             response = session.get(url, headers=headers, params=params)
#             if response.status_code == 401:
#                 new_token = refresh_zoho_access_token()
#                 headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#                 response = session.get(url, headers=headers, params=params)
#             response.raise_for_status()
#             items = response.json()
#             items_to_get.extend(items.get('salesorders', []))
#             if not items.get('page_context', {}).get('has_more_page', False):
#                 break
#             params['page'] += 1
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Error fetching sales orders: {e}")
#             return JsonResponse({'error': 'Failed to fetch sales orders'}, status=500)
    
#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         futures = [executor.submit(fetch_sales_order_details, item, session, headers) for item in items_to_get]
#         full_items_to_get = [future.result() for future in as_completed(futures) if future.result()]
    
#     salesorder_ids = [item['salesorder_id'] for item in full_items_to_get]
#     existing_orders = ZohoInventoryShipmentSalesOrder.objects.filter(salesorder_id__in=salesorder_ids)
#     existing_salesorder_ids = set(existing_orders.values_list('salesorder_id', flat=True))

#     new_sales_orders = []
#     sales_orders_to_update = []
    
#     for data in full_items_to_get:
#         new_item = create_inventory_sales_order_instance(logger, data)
#         if new_item.salesorder_id in existing_salesorder_ids:
#             sales_orders_to_update.append(new_item)
#         else:
#             new_sales_orders.append(new_item)

#     with transaction.atomic():
#         if new_sales_orders:
#             ZohoInventoryShipmentSalesOrder.objects.bulk_create(new_sales_orders, ignore_conflicts=True, batch_size=200)
#         if sales_orders_to_update:
#             ZohoInventoryShipmentSalesOrder.objects.bulk_update(
#                 sales_orders_to_update,
#                 fields=[
#                     'salesorder_number', 'date', 'status', 'customer_id', 'customer_name',
#                     'is_taxable', 'tax_id', 'tax_name', 'tax_percentage', 'currency_id',
#                     'currency_code', 'currency_symbol', 'exchange_rate', 'delivery_method',
#                     'total_quantity', 'sub_total', 'tax_total', 'total', 'created_by_email',
#                     'created_by_name', 'salesperson_id', 'salesperson_name', 'is_test_order',
#                     'notes', 'payment_terms', 'payment_terms_label', 'line_items',
#                     'shipping_address', 'billing_address', 'warehouses', 'custom_fields',
#                     'order_sub_statuses', 'shipment_sub_statuses', 'created_time',
#                     'last_modified_time'
#                 ],
#                 batch_size=200
#             )
#     if username:        
#         module='zoho_sales_orders'
#         info='has loaded new info from Zoho Sales Orders'
#         type='load'
#         create_notification(module, info, type, username)
    
#     return JsonResponse({'message': 'Sales Orders loaded successfully'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_sales_orders(request):
    data = json.loads(request.body)
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    username = data.get('username')
    if not start_date:
        return JsonResponse({'error': 'Date is missing'}, status=400)
    out = sync_inventory_sales_orders(start_date=start_date, end_date=end_date, username=username)
    if username:        
        module='zoho_sales_orders'
        info='has loaded new info from Zoho Sales Orders'
        type='load'
        create_notification(module, info, type, username)
    return JsonResponse({'message': 'Sales Orders loaded successfully', **out}, status=200)


#############################################
# FETCH SHIPMENTS AND PACKAGES
#############################################

# @retry(
#     retry=retry_if_exception_type(requests.exceptions.RequestException),
#     wait=wait_exponential(multiplier=1, min=4, max=60),
#     stop=stop_after_attempt(5)
# )
# def fetch_package(package_id, session, headers):
#     url = f'{settings.ZOHO_INVENTORY_PACKAGES_URL}/{package_id}'
#     try:
#         response = session.get(url, headers=headers, params={})
#         if response.status_code == 401:
#             new_token = refresh_zoho_access_token()
#             headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#             response = session.get(url, headers=headers, params={})
#         if response.status_code == 429:
#             logger.warning(f"Rate limit exceeded when fetching package {package_id}. Retrying...")
#             time.sleep(10)
#             response.raise_for_status()
#         if response.status_code >= 400:
#             logger.error(f"Error 1 fetching the package: {response.text}")
#             return JsonResponse({'error': 'Failed to fetch shipments'}, status=500)
#         response.raise_for_status()
#         item = response.json()
#         return item.get('package', None)
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Error 2 fetching shipments: {e}")
#         raise
#         # return JsonResponse({'error': 'Failed to fetch shipments'}, status=500)
    
# @retry(
#     retry=retry_if_exception_type(requests.exceptions.RequestException),
#     wait=wait_exponential(multiplier=1, min=4, max=60),
#     stop=stop_after_attempt(5)
# )
# def fetch_shipment_details(item, session, headers):
#     try:
#         url = f'{settings.ZOHO_INVENTORY_SHIPMENTS_URL}/{item["shipment_id"]}'
#         response = session.get(url, headers=headers, params={})
#         if response.status_code == 401:
#             new_token = refresh_zoho_access_token()
#             headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#             response = session.get(url, headers=headers, params={})
#         if response.status_code == 429:
#             logger.warning(f"Rate limit exceeded when fetching shipment {item['shipment_id']}. Retrying...")
#             time.sleep(10)
#             response.raise_for_status()
#         response.raise_for_status()
#         full_item = response.json()
#         return full_item.get('shipmentorder', None)
#     except Exception as e:
#         logger.error(f"Error fetching details for shipment {item['shipment_id']}: {e}")
#         raise
#         # return None
    

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def load_inventory_shipments(request):
#     MAX_WORKERS = 5
#     app_config = AppConfig.objects.first()
#     logger.debug(app_config)
#     try:
#         headers = config_headers()
#     except Exception as e:
#         logger.error(f"Error connecting to Zoho API: {str(e)}")
#         return JsonResponse({'error': f"Error connecting to Zoho API (Load Shipments): {str(e)}"}, status=500)

#     data = json.loads(request.body)
#     start_date = data.get('start_date', None)
#     end_date = data.get('end_date', None)
#     username = data.get('username', None)
    
#     logger.debug(f"Start date: {start_date}, End date: {end_date}")
    
#     try:
#         if start_date:
#             dt.strptime(start_date, '%Y-%m-%d')
#         if end_date:
#             dt.strptime(end_date, '%Y-%m-%d')
#     except ValueError:
#         logger.error('Invalid date format')
#         return JsonResponse({'error': 'Invalid date format'}, status=400)
    
#     params = {
#         'organization_id': app_config.zoho_org_id,
#         'per_page': 200,
#         'page': 1,
#     }
#     if end_date and start_date:
#         params.update({'date_start': start_date, 'date_end': end_date})
#     elif start_date:
#         params['date'] = start_date

#     url = settings.ZOHO_INVENTORY_SHIPMENTS_URL
#     items_to_get = []
#     session = requests.Session()
    
#     while True:
#         try:
#             response = session.get(url, headers=headers, params=params)
#             if response.status_code == 401:
#                 new_token = refresh_zoho_access_token()
#                 headers['Authorization'] = f'Zoho-oauthtoken {new_token}'
#                 response = session.get(url, headers=headers, params=params)
#             if response.status_code >= 400:
#                 logger.error(f"Error fetching shipments: {response.text}")
#                 return JsonResponse({'error': 'Failed to fetch shipments'}, status=500)
#             items = response.json()
#             items_to_get.extend(items.get('shipmentorders', []))
#             if not items.get('page_context', {}).get('has_more_page', False):
#                 break
#             params['page'] += 1
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Error fetching shipments: {e}")
#             return JsonResponse({'error': 'Failed to fetch shipments'}, status=500)
    
#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         futures = [executor.submit(fetch_shipment_details, item, session, headers) for item in items_to_get]
#         full_items_to_get = [future.result() for future in as_completed(futures) if future.result()]
    
#     all_package_ids = []
#     for data in full_items_to_get:
#         pkg_info = data.get('packages', [])
#         if pkg_info:
#             package_ids = [pkg.get('package_id') for pkg in pkg_info if pkg.get('package_id')]
#             all_package_ids.extend(package_ids)
    
#     all_package_ids = list(set(all_package_ids))
    
#     existing_packages = ZohoPackage.objects.filter(package_id__in=all_package_ids)
#     existing_packages_ids = set(existing_packages.values_list('package_id', flat=True))
    
#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         future_to_package_id = {executor.submit(fetch_package, pkg_id, session, headers): pkg_id for pkg_id in all_package_ids}
#         all_packages_data = []
#         for future in as_completed(future_to_package_id):
#             pkg_id = future_to_package_id[future]
#             try:
#                 pkg_data = future.result()
#                 if pkg_data:
#                     all_packages_data.append(pkg_data)
#             except Exception as exc:
#                 logger.error(f"Error fetching package {pkg_id}: {exc}")
    
#     new_packages = []
#     packages_to_update = []
#     for pkg_data in all_packages_data:
#         new_pkg = create_inventory_package_instance(logger, pkg_data)
#         if new_pkg.package_id in existing_packages_ids:
#             packages_to_update.append(new_pkg)
#         else:
#             new_packages.append(new_pkg)
    
#     shipments_ids = [item['shipment_id'] for item in full_items_to_get if item.get('shipment_id')]
#     existing_shipments = ZohoShipmentOrder.objects.filter(shipment_id__in=shipments_ids)
#     existing_shipments_ids = set(existing_shipments.values_list('shipment_id', flat=True))

#     new_shipments = []
#     shipments_to_update = []
#     for data in full_items_to_get:
#         new_item = create_inventory_shipment_instance(logger, data)
#         if new_item.shipment_id in existing_shipments_ids:
#             shipments_to_update.append(new_item)
#         else:
#             new_shipments.append(new_item)
    
#     shipment_fields_to_update = [
#                     'salesorder_id',
#                     'salesorder_number',
#                     'salesorder_date',
#                     'salesorder_fulfilment_status',
#                     'sales_channel',
#                     'sales_channel_formatted',
#                     'shipment_number',
#                     'date',
#                     'shipment_status',
#                     'shipment_sub_status',
#                     'status',
#                     'detailed_status',
#                     'status_message',
#                     'carrier',
#                     'tracking_carrier_code',
#                     'service',
#                     'delivery_days',
#                     'source_id',
#                     'label_format',
#                     'source_name',
#                     'delivery_guarantee',
#                     'reference_number',
#                     'customer_id',
#                     'customer_name',
#                     'is_taxable',
#                     'tax_id',
#                     'tax_name',
#                     'tax_percentage',
#                     'currency_id',
#                     'currency_code',
#                     'currency_symbol',
#                     'exchange_rate',
#                     'discount',
#                     'is_discount_before_tax',
#                     'discount_type',
#                     'estimate_id',
#                     'delivery_method',
#                     'delivery_method_id',
#                     'tracking_number',
#                     'tracking_link',
#                     'last_tracking_update_date',
#                     'expected_delivery_date',
#                     'shipment_delivered_date',
#                     'shipment_type',
#                     'is_carrier_shipment',
#                     'is_tracking_enabled',
#                     'is_forms_available',
#                     'is_email_notification_enabled',
#                     'shipping_charge',
#                     'sub_total',
#                     'tax_total',
#                     'total',
#                     'price_precision',
#                     'is_emailed',
#                     'notes',
#                     'template_id',
#                     'template_name',
#                     'template_type',
#                     'created_time',
#                     'last_modified_time',
#                     'associated_packages_count',
#                     'created_by_id',
#                     'last_modified_by_id',
#                     'contact_persons',
#                     'invoices',
#                     'line_items',
#                     'packages',
#                     'billing_address',
#                     'shipping_address',
#                     'custom_fields',
#                     'custom_field_hash',
#                     'documents',
#                     'taxes',
#                     'tracking_statuses',
#                     'multipiece_shipments',
#     ]
#     package_fields_to_update = [
#                     'salesorder_id',
#                     'salesorder_number',
#                     'salesorder_date',
#                     'sales_channel',
#                     'sales_channel_formatted',
#                     'salesorder_fulfilment_status',
#                     'shipment_id',
#                     'shipment_number',
#                     'shipment_order',
#                     'package_number',
#                     'date',
#                     'shipping_date',
#                     'delivery_method',
#                     'delivery_method_id',
#                     'tracking_number',
#                     'tracking_link',
#                     'expected_delivery_date',
#                     'shipment_delivered_date',
#                     'status',
#                     'detailed_status',
#                     'status_message',
#                     'carrier',
#                     'service',
#                     'delivery_days',
#                     'delivery_guarantee',
#                     'total_quantity',
#                     'customer_id',
#                     'customer_name',
#                     'email',
#                     'phone',
#                     'mobile',
#                     'contact_persons',
#                     'created_by_id',
#                     'last_modified_by_id',
#                     'created_time',
#                     'last_modified_time',
#                     'notes',
#                     'terms',
#                     'is_emailed',
#                     'is_advanced_tracking_missing',
#                     'line_items',
#                     'custom_fields',
#                     'custom_field_hash',
#                     'shipmentorder_custom_fields',
#                     'billing_address',
#                     'shipping_address',
#                     'picklists',
#                     'template_id',
#                     'template_name',
#                     'template_type',
#     ]
    
#     logger.info(f"New shipments: {len(new_shipments)}, Shipments to update: {len(shipments_to_update)}")

#     with transaction.atomic():
#         if new_shipments:
#             ZohoShipmentOrder.objects.bulk_create(new_shipments, ignore_conflicts=True, batch_size=200)
#         if shipments_to_update:
#             ZohoShipmentOrder.objects.bulk_update(shipments_to_update, fields=shipment_fields_to_update, batch_size=200)
#         if new_packages:
#             ZohoPackage.objects.bulk_create(new_packages, ignore_conflicts=True, batch_size=200)
#         if packages_to_update:
#             ZohoPackage.objects.bulk_update(packages_to_update, fields=package_fields_to_update, batch_size=200)
            
#     previous_day = timezone.now()
    
#     JobsUpdatingTimes.objects.filter(last_updated__lt=previous_day).delete()
            
#     JobsUpdatingTimes.objects.create(last_updated=timezone.now())
    
#     if username:
#         module='zoho_shipment'
#         info='has loaded new info from Zoho Shipments'
#         type='load'
#         create_notification(module, info, type, username)
            
#     logger.info(f"Shipments processed successfully: {len(new_shipments)} created, {len(shipments_to_update)} updated")

#     return JsonResponse({'message': 'Shipments loaded successfully'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def load_inventory_shipments(request):
    data = json.loads(request.body)
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    username = data.get('username')
    out = sync_inventory_shipments(start_date=start_date, end_date=end_date, username=username, updated_since=None)
    if username:
        module='zoho_shipment'
        info='has loaded new info from Zoho Shipments'
        type='load'
        create_notification(module, info, type, username)
    return JsonResponse({'message': 'Shipments loaded successfully', **out}, status=200)


#############################################
# SYNC ITEMS WITH SENITRON
############################################# 


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
# DELETE USER
#############################################  

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_user(request, user_id):
    data = request.data
    payload_username = data.get('username', None)
    user = LoginUser.objects.filter(id=user_id).first()
    deleted_username = user.username
    if not user:
        return JsonResponse({'error': 'User not found'}, status=404)
    user.delete()
    if payload_username:
        module='delete_system_user'
        info=f'has deleted user: {deleted_username}'
        type='delete_system_user'
        create_notification(module, info, type, payload_username)
    return JsonResponse({'message': 'User deleted successfully'}, status=200) 


@csrf_exempt
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_users(request):
    data = request.data
    print('Data', data)
    user_ids = data.get('user_ids', [])
    payload_username = data.get('username', None)
    if not user_ids:
        return JsonResponse({'error': 'User ids are missing'}, status=400)
    users = LoginUser.objects.filter(id__in=user_ids)
    deleted_usernames = list(users.values_list('username', flat=True))
    deleted_usernames = ', '.join(deleted_usernames)
    if not users:
        return JsonResponse({'error': 'Users not found'}, status=404)
    users.delete()
    if payload_username:
        module='delete_system_users'
        info=f'has deleted user(s): {deleted_usernames}'
        type='delete_system_users'
        create_notification(module, info, type, payload_username)
    return JsonResponse({'message': 'Users deleted successfully'}, status=200)

#############################################
# CREATE ZOHO TRACK INFO
############################################# 

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_zoho_sku_track_info(request):
    last_sku_track_info = ZohoSkuTrackInfo.objects.last()
    data = json.loads(request.body)
    sku_tracked = data.get('sku_tracked', 0)
    sku_matched = data.get('sku_matched', 0)
    sku_missing = data.get('sku_missing', 0)
    sku_excess = data.get('sku_excess', 0)
    if not last_sku_track_info:
        ZohoSkuTrackInfo.objects.create(
            sku_tracked=sku_tracked,
            sku_matched=sku_matched,
            sku_missing=sku_missing,
            sku_excess=sku_excess   
        ).save()
        message = 'SKU track info created successfully'
    elif last_sku_track_info.sku_tracked != sku_tracked or \
         last_sku_track_info.sku_matched != sku_matched or \
         last_sku_track_info.sku_missing != sku_missing or \
         last_sku_track_info.sku_excess != sku_excess:
        ZohoSkuTrackInfo.objects.create(
            sku_tracked=sku_tracked,
            sku_matched=sku_matched,
            sku_missing=sku_missing,
            sku_excess=sku_excess
        ).save()
        message = 'SKU track info updated successfully'
    else:
        message = 'SKU track info already exists'
    return JsonResponse({'message': message}, status=201)



#############################################
# CREATE ZOHO ITEMS ASSETS TRACK
############################################# 

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_zoho_items_assets_track(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    info = payload.get('items', []) or []
    if not info:
        return JsonResponse({'message': 'No Items Assets Info to save'}, status=201)

    latest_created_time = ZohoItemAssetsTrack.objects.aggregate(Max('created_time'))['created_time__max']
    previous_day = None
    if latest_created_time:
        if timezone.is_naive(latest_created_time):
            latest_created_time = timezone.make_aware(latest_created_time, timezone.get_current_timezone())
        previous_day = latest_created_time - timedelta(days=1)

    now_ts = timezone.now()

    items_to_insert = []
    for row in info:
        obj = create_zoho_item_assets_track_instance(logger, row, now_ts)
        if obj is not None:                      # <-- evita meter None
            items_to_insert.append(obj)

    if not items_to_insert:
        return JsonResponse({'message': 'No valid Items Assets Info to save'}, status=201)

    with transaction.atomic():
        if previous_day is not None:
            deleted_count, _ = ZohoItemAssetsTrack.objects.filter(created_time__lt=previous_day).delete()
            logger.info(f"Deleted {deleted_count} old ZohoItemAssetsTrack records.")
        
        ZohoItemAssetsTrack.objects.bulk_create(
            items_to_insert,
            batch_size=200,
            ignore_conflicts=True,
        )

    return JsonResponse({'message': 'Items Assets Info saved successfully'}, status=201)


#############################################
# IGNORE SELECTED ERRORS
#############################################

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def ignore_selected_errors_zoho_items(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    errors = data.get('errors', [])
    new_value = data.get('new_value', False)
    
    if not isinstance(errors, list):
        return JsonResponse({'error': 'Errors should be a list'}, status=400)
    
    if not isinstance(new_value, bool):
        return JsonResponse({'error': 'new_value should be a boolean'}, status=400)
    
    if not errors:
        return JsonResponse({'error': 'Errors are missing'}, status=400)
    
    instances = ZohoInventoryItem.objects.filter(item_id__in=errors)
    
    if not instances.exists():
        return JsonResponse({'error': 'Items not found'}, status=404)
    
    updated_count = instances.update(ignore_errors=new_value)
    
    return JsonResponse({'message': f'{updated_count} items updated successfully'}, status=200)


#############################################
# MANUAL UPDATING JOBS STATUS
#############################################

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def set_manual_updating_jobs(request):
    
    now = timezone.now()
    
    data = json.loads(request.body)
    
    is_running = data.get('is_running', False)
    
    updating_job = ManualUpdatingJobs.objects.first()
    if not updating_job:
        updating_job = ManualUpdatingJobs.objects.create()
    updating_job.is_running = is_running
    updating_job.last_updated = now
    updating_job.save()
    
    return JsonResponse({'message': f'Jobs updated successfully'}, status=200)


def force_rollback_manual_update():
    now = timezone.now()
    updating_job = ManualUpdatingJobs.objects.first()
    if not updating_job:
        updating_job = ManualUpdatingJobs.objects.create()
    if updating_job.is_running:
        last_updated = updating_job.last_updated
        if last_updated:
            if timezone.is_naive(last_updated):
                last_updated = timezone.make_aware(last_updated, timezone.get_current_timezone())
            if now - last_updated > timedelta(minutes=1):
                updating_job.is_running = False
                updating_job.last_updated = now
                updating_job.save()
    return
    

#############################################
# EXTRA FUNCTIONS  
#############################################
