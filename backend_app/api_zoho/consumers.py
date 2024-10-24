# api_zoho/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class InventoryItemConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "inventory_items",  # Nombre del grupo
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "inventory_items",
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def send_item_update(self, event):
        await self.send(text_data=json.dumps(event["message"]))
        

class InventorySalesOrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "inventory_sales_order",  
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "inventory_sales_order",
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def send_sales_order_update(self, event):
        await self.send(text_data=json.dumps(event["message"]))
