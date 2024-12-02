from celery import shared_task
from datetime import datetime
from django.http import HttpRequest
from .views import load_inventory_shipments, load_inventory_items
import json

@shared_task
def task_load_inventory_shipments():
    start_date = datetime.now().strftime("%Y-%m-%d")
    data = {'start_date': start_date}
    request = HttpRequest()
    request.method = 'POST'
    request.content_type = 'application/json'
    request._body = json.dumps(data).encode('utf-8')
    load_inventory_shipments(request)
    
    
@shared_task
def task_load_inventory_items():
    request = HttpRequest()
    request.method = 'POST'
    request.content_type = 'application/json'
    request._body = json.dumps({}).encode('utf-8')
    load_inventory_items(request)