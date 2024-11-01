# api_zoho/routing.py
from django.urls import path
from .consumers import SenitronInventoryItemConsumer, SenitronInventoryItemsAssetsConsumer, SenitronTimelineConsumer

websocket_senitron_urlpatterns = [
    path('api_zoho_senitron/ws/senitron_inventory_items/', SenitronInventoryItemConsumer.as_asgi(), name='ws_senitron_inventory_items'),
    path('api_zoho_senitron/ws/senitron_inventory_items_assets/', SenitronInventoryItemsAssetsConsumer.as_asgi(), name='ws_senitron_inventory_items_assets'),
    path('api_zoho_senitron/ws/senitron_timelines/', SenitronTimelineConsumer.as_asgi(), name='ws_senitron_timelines'),
]
