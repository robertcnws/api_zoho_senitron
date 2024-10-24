# api_zoho/routing.py
from django.urls import path
from .consumers import InventoryItemConsumer, InventorySalesOrderConsumer

websocket_urlpatterns = [
    path('api_zoho_senitron/ws/inventory_items/', InventoryItemConsumer.as_asgi(), name='ws_inventory_items'),
    path('api_zoho_senitron/ws/inventory_sales_orders/', InventorySalesOrderConsumer.as_asgi(), name='ws_inventory_sales_orders'),
]
