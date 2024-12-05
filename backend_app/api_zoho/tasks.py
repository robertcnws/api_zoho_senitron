from celery import shared_task
from datetime import datetime
from django.http import HttpRequest
from django.utils import timezone
from .views import load_inventory_shipments, load_inventory_items, force_rollback_manual_update
from .models import JobsUpdatingTimes
import json
    
@shared_task
def task_load_inventory_items():
    request = HttpRequest()
    request.method = 'POST'
    request.content_type = 'application/json'
    request._body = json.dumps({}).encode('utf-8')
    load_inventory_items(request)
    
@shared_task
def task_load_inventory_shipments():
    start_date = datetime.now().strftime("%Y-%m-%d")
    data = {'start_date': start_date}
    request = HttpRequest()
    request.method = 'POST'
    request.content_type = 'application/json'
    request._body = json.dumps(data).encode('utf-8')
    load_inventory_shipments(request)
    JobsUpdatingTimes.objects.create(last_updated=timezone.now())
    

@shared_task    
def task_force_rollback_manual_update():
    force_rollback_manual_update()