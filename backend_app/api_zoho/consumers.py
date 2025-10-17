# api_zoho/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

ALLOWED_GROUPS = {
    "inventory_items",
    "inventory_sales_order",
    "login_users",
    "inventory_shipment_order",
    "inventory_packages",
    "inventory_sku_track_info",
    "inventory_item_assets_track",
    "jobs_updating_times",
    "manual_updating_jobs",
}

EVENT_TYPES = (
    "send_item_update",
    "send_sales_order_update",
    "send_login_user_update",
    "send_shipment_order_update",
    "send_package_update",
    "send_sku_track_update",
    "send_item_assets_track_update",
    "send_jobs_updating_times_update",
    "send_manual_updating_jobs_update",
)

class GenericZohoGroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group = self.scope["url_route"]["kwargs"]["group"]
        if self.group not in ALLOWED_GROUPS:
            await self.close(code=4001)
            return
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group") and self.group in ALLOWED_GROUPS:
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        pass

    async def _forward(self, event):
        await self.send(text_data=json.dumps(event["message"]))
        
for _name in EVENT_TYPES:
    async def _mk(self, event, __f=GenericZohoGroupConsumer._forward):
        await __f(self, event)
    setattr(GenericZohoGroupConsumer, _name, _mk)