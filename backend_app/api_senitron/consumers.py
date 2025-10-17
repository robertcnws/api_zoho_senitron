# api_zoho/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

ALLOWED_GROUPS = {
    "senitron_inventory_items",
    "senitron_inventory_items_assets",
    "senitron_timelines",
    "senitron_inventory_items_asset_logs",
    "notification_users",
}

EVENT_TYPES = (
    "send_senitron_item_update",
    "send_senitron_item_asset_update",
    "send_senitron_timeline_update",
    "send_senitron_item_asset_log_update",
    "send_notification_user_update",
)

class GenericSenitronGroupConsumer(AsyncWebsocketConsumer):
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
    async def _mk(self, event, __f=GenericSenitronGroupConsumer._forward):
        await __f(self, event)
    setattr(GenericSenitronGroupConsumer, _name, _mk)