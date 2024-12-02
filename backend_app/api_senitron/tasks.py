from celery import shared_task
from datetime import datetime
from django.http import HttpRequest
from .views import load_senitron_inventory_item_assets
import json

@shared_task
def task_load_senitron_inventory_item_assets():
    request = HttpRequest()
    request.method = 'POST'
    request.content_type = 'application/json'
    request._body = json.dumps({}).encode('utf-8')
    load_senitron_inventory_item_assets(request)