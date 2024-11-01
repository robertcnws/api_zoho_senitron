# api_zoho/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class SenitronInventoryItemConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "senitron_inventory_items",  # Nombre del grupo
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "senitron_inventory_items",
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def send_senitron_item_update(self, event):
        await self.send(text_data=json.dumps(event["message"]))
        

class SenitronInventoryItemsAssetsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "senitron_inventory_items_assets",  
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "senitron_inventory_items_assets",
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def send_senitron_item_asset_update(self, event):
        await self.send(text_data=json.dumps(event["message"]))
        

class SenitronTimelineConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "senitron_timeline",  
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "senitron_timeline",
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def send_senitron_timeline_update(self, event):
        await self.send(text_data=json.dumps(event["message"]))
