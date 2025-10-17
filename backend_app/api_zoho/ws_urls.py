# api_zoho/routing.py
from django.urls import path
from .consumers import GenericZohoGroupConsumer

websocket_urlpatterns = [
    path('api_zoho_senitron/ws/inventory_items/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "inventory_items"}),
    path('api_zoho_senitron/ws/inventory_sales_orders/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "inventory_sales_order"}),
    path('api_zoho_senitron/ws/users/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "login_users"}),
    path('api_zoho_senitron/ws/shipment_orders/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "inventory_shipment_order"}),
    path('api_zoho_senitron/ws/packages/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "inventory_packages"}),
    path('api_zoho_senitron/ws/sku_track_info/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "inventory_sku_track_info"}),
    path('api_zoho_senitron/ws/item_assets_track/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "inventory_item_assets_track"}),
    path('api_zoho_senitron/ws/jobs_updating_times/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "jobs_updating_times"}),
    path('api_zoho_senitron/ws/manual_updating_jobs/', GenericZohoGroupConsumer.as_asgi(), kwargs={"group": "manual_updating_jobs"}),
]
