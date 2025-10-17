# api_zoho/routing.py
from django.urls import path
from .consumers import GenericSenitronGroupConsumer

websocket_senitron_urlpatterns = [
    path(
        'api_zoho_senitron/ws/senitron_inventory_items/', 
        GenericSenitronGroupConsumer.as_asgi(), 
        kwargs={"group": "senitron_inventory_items"}
    ),
    path(
        'api_zoho_senitron/ws/senitron_inventory_items_assets/', 
        GenericSenitronGroupConsumer.as_asgi(), 
        kwargs={"group": "senitron_inventory_items_assets"},
    ),
    path(
        'api_zoho_senitron/ws/senitron_timelines/', 
        GenericSenitronGroupConsumer.as_asgi(), 
        kwargs={"group": "senitron_timelines"},
    ),
    path(
        'api_zoho_senitron/ws/senitron_inventory_items_asset_logs/', 
        GenericSenitronGroupConsumer.as_asgi(), 
        kwargs={"group": "senitron_inventory_items_asset_logs"},
    ),
    path(
        'api_zoho_senitron/ws/notification_users/', 
        GenericSenitronGroupConsumer.as_asgi(), 
        kwargs={"group": "notification_users"},
    ),
]
